import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from tastyworks.models.option import Option, OptionType
from tastyworks.models.underlying import UnderlyingType

import aiohttp
from dataclasses import dataclass, field

from tastyworks.models.security import Security

LOGGER = logging.getLogger(__name__)


class OrderType(Enum):
    LIMIT = 'Limit'
    MARKET = 'Market'
    STOP_LIMIT = 'Stop Limit'
    STOP = 'Stop'


class OrderPriceEffect(Enum):
    CREDIT = 'Credit'
    DEBIT = 'Debit'


class OrderStatus(Enum):
    RECEIVED = 'Received'
    CANCELLED = 'Cancelled'
    FILLED = 'Filled'
    EXPIRED = 'Expired'
    LIVE = 'Live'
    REJECTED = 'Rejected'
    CANCEL_REQUESTED = 'Cancel Requested'

    def is_active(self):
        return self in (OrderStatus.LIVE, OrderStatus.RECEIVED, OrderStatus.CANCEL_REQUESTED)


class TimeInForce(Enum):
    DAY = 'Day'
    GTC = 'GTC'
    GTD = 'GTD'


@dataclass
class OrderDetails(object):
    order_id = None
    ticker = None
    type: OrderType = None
    time_in_force: TimeInForce = TimeInForce.DAY
    gtc_date: datetime = None
    price: Decimal = None
    stop_trigger: Decimal = None
    price_effect: OrderPriceEffect = None
    status: OrderStatus = None
    legs: List[Security] = field(default_factory=list)
    source: str = 'WBT'

    def is_executable(self) -> bool:
        required_data = all([
            self.time_in_force,
            self.type,
            self.source
        ])

        if self.type == OrderType.STOP or self.type == OrderType.MARKET:
            non_stop_required_data = all([
                self.price_effect,
                self.price is None
            ])
        else:
            non_stop_required_data = all([
                self.price_effect,
                self.price is not None
            ])

        if not required_data:
            return False

        if not non_stop_required_data:
            return False

        if not self.legs:
            return False

        if self.time_in_force == TimeInForce.GTD:
            try:
                datetime.strptime(self.gtc_date, '%Y-%m-%d')
            except ValueError:
                return False

        return True


class Order(Security):
    def __init__(self, order_details: OrderDetails):
        """
        Initiates a new order object.

        Args:
            order_details (OrderDetails): An object specifying order-level details.
        """
        self.details = order_details

    def check_is_order_executable(self):
        return self.details.is_executable()

    def add_leg(self, security: Security):
        self.details.legs.append(security)

    def get_equity_leg_from_dict(self, input_dict: dict):
        exp_date = datetime.strptime(input_dict['symbol'][6:12], '%y%m%d').date()
        option_type = OptionType(input_dict['symbol'][12:13])
        strike = Decimal(input_dict['symbol'][13:]) / 1000
        return Option(ticker=self.details.ticker, quantity=input_dict['quantity'], expiry=exp_date, strike=strike, option_type=option_type, underlying_type=UnderlyingType.EQUITY)

    @classmethod
    def from_dict(cls, input_dict: dict):
        """
        Parses an Order object from a dict.
        """
        details = OrderDetails(input_dict['underlying-symbol'])
        details.order_id = input_dict['id'] if 'id' in input_dict else None
        details.ticker = input_dict['underlying-symbol'] if 'underlying-symbol' in input_dict else None
        details.price = Decimal(input_dict['price']) if 'price' in input_dict else None
        details.stop_trigger = Decimal(input_dict['stop-trigger']) if 'stop-trigger' in input_dict else None
        details.price_effect = OrderPriceEffect(input_dict['price-effect']) if 'price-effect' in input_dict else None
        details.type = OrderType(input_dict['order-type'])
        details.status = OrderStatus(input_dict['status'])
        details.time_in_force = input_dict['time-in-force']
        details.gtc_date = input_dict.get('gtc-date', None)
        order = cls(order_details=details)
        for leg in input_dict['legs']:
            if leg['instrument-type'] == 'Equity Option':
                leg_obj = order.get_equity_leg_from_dict(leg)
                order.details.legs.append(leg_obj)
        return order

    @classmethod
    async def get_remote_orders(cls, session, account, **kwargs) -> List:
        """
        Gets all orders on Tastyworks.

        Args:
            session (TastyAPISession): The session to use.
            account (TradingAccount): The account_id to get orders on.
            Keyword arguments specifying filtering conditions, these include:
            `status`, `time-in-force`, etc.

        Returns:
            list(Order): A list of Orders
        """
        if not session.logged_in:
            raise Exception('Tastyworks session not logged in.')

        filters = kwargs
        url = '{}/accounts/{}/orders'.format(
            session.API_url,
            account.account_number
        )
        url = '{}?{}'.format(
            url,
            '&'.join([f'{k}={v}' for k, v in filters.items()])
        )

        res = []
        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as resp:
            if resp.status != 200:
                raise Exception('Could not get current open orders')
            data = (await resp.json())['data']['items']
            for order_data in data:
                order = cls.from_dict(order_data)
                res.append(order)
        return res

    @classmethod
    async def get_live_orders(cls, session, account, **kwargs) -> List:
        """
        Gets all live orders on Tastyworks.

        Args:
            session (TastyAPISession): The session to use.
            account (TradingAccount): The account_id to get orders on.
            Keyword arguments specifying filtering conditions, these include:
            `status`, `time-in-force`, etc.

        Returns:
            list(Order): A list of Orders
        """
        if not session.logged_in:
            raise Exception('Tastyworks session not logged in.')

        filters = kwargs
        url = '{}/accounts/{}/orders/live'.format(
            session.API_url,
            account.account_number
        )
        url = '{}?{}'.format(
            url,
            '&'.join([f'{k}={v}' for k, v in filters.items()])
        )

        res = []
        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as resp:
            if resp.status != 200:
                raise Exception('Could not get current open orders')
            data = (await resp.json())['data']['items']
            for order_data in data:
                order = cls.from_dict(order_data)
                if not order.details.status.is_active():
                    continue
                res.append(order)
        return res

    @classmethod
    async def cancel_order(cls, session, account, order_id):
        """
        cancels an order on Tastyworks.

        Args:
            session (TastyAPISession): The session to use.
            account (TradingAccount): The account_id to get orders on.
            order_id (OrderDetails): The order_id returned from get_remote_orders.

        Returns:
            A single order. The order will have a cancalled status if successfull.
        """
        if not session.logged_in:
            raise Exception('Tastyworks session not logged in.')

        url = '{}/accounts/{}/orders/{}'.format(
            session.API_url,
            account.account_number,
            order_id
        )

        async with aiohttp.request('DELETE', url, headers=session.get_request_headers()) as resp:
            if resp.status != 200:
                raise Exception('Could not delete the order')
            data = (await resp.json())['data']
            order = cls.from_dict(data)
            return order.details.status

    @classmethod
    async def get_order(cls, session, account, order_id):
        """
        gets an order by the order id on Tastyworks.

        Args:
            session (TastyAPISession): The session to use.
            account (TradingAccount): The account_id to get orders on.
            order_id (OrderDetails): The order_id returned from get_remote_orders.

        Returns:
            A single order. The order will have a cancalled status if successfull.
        """
        if not session.logged_in:
            raise Exception('Tastyworks session not logged in.')

        url = '{}/accounts/{}/orders/{}'.format(
            session.API_url,
            account.account_number,
            order_id
        )

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as resp:
            if resp.status != 200:
                raise Exception('Could not retreive the order')
            data = (await resp.json())['data']
            order = cls.from_dict(data)
            return order
