import logging
from decimal import Decimal
from enum import Enum
from typing import List

import aiohttp
from dataclasses import dataclass, field

from tastyworks.models.security import Security

LOGGER = logging.getLogger(__name__)


class OrderType(Enum):
    LIMIT = 'Limit'
    MARKET = 'Market'
    STOP_LIMIT = 'Stop Limit'
    STOP_MARKET = 'Stop'

    def is_limit(self):
        return self in (OrderType.LIMIT, OrderType.STOP_LIMIT)
    def is_stop(self):
        return self in (OrderType.STOP_LIMIT, OrderType.STOP_MARKET)
    def is_market(self):
        return self in (OrderType.MARKET, OrderType.STOP_MARKET)

    @classmethod
    def from_str(cls, str_rep):
        return getattr(cls, str_rep.replace('_', ' ', 1).upper(), None)

class OrderPriceEffect(Enum):
    CREDIT = 'Credit'
    DEBIT = 'Debit'

    @classmethod
    def from_str(cls, str_rep):
        return getattr(cls, str_rep.upper(), None)


class OrderStatus(Enum):
    RECEIVED = 'Received'
    CANCELLED = 'Cancelled'
    FILLED = 'Filled'
    EXPIRED = 'Expired'
    LIVE = 'Live'
    REJECTED = 'Rejected'
    ROUTED = 'Routed'

    @classmethod
    def from_str(cls, str_rep):
        return getattr(cls, str_rep.upper(), None)

    def is_active(self):
        return self in (OrderStatus.LIVE, OrderStatus.RECEIVED)

    def is_filled(self):
        return self == OrderStatus.FILLED

@dataclass
class OrderDetails(object):
    type: OrderType = None
    is_open_order: bool = field(default=True)
    time_in_force: str = 'Day'
    price: Decimal = None
    stop_trigger: Decimal = None
    price_effect: OrderPriceEffect = None
    status: OrderStatus = None
    legs: List[Security] = field(default_factory=list)
    source: str = 'WBT'

    def is_executable(self) -> bool:
        required_data = all([
            self.time_in_force,
            self.price_effect,
            self.price is not None,
            self.type,
            self.source
        ])

        if not required_data:
            return False

        if not self.legs:
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

    @classmethod
    def from_dict(cls, input_dict: dict):
        """
        Parses an Order object from a dict.
        """
        details = OrderDetails(input_dict['underlying-symbol'])
        details.price = Decimal(input_dict['price'])
        details.price_effect = OrderPriceEffect(input_dict['price-effect'])
        details.type = OrderType(input_dict['order-type'])
        details.status = OrderStatus(input_dict['status'])
        details.time_in_force = input_dict['time-in-force']
        return cls(
            order_details=details
        )

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
                if not order.details.status.is_active():
                    continue
                res.append(order)
        return res
