import logging
from datetime import datetime
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

    def is_active(self):
        return self in (OrderStatus.LIVE, OrderStatus.RECEIVED)


class TimeInForce(Enum):
    DAY = 'Day'
    GTC = 'GTC'
    GTD = 'GTD'


@dataclass
class OrderDetails(object):
    """Class for storing an order details."""
    type: OrderType = None
    time_in_force: TimeInForce = TimeInForce.DAY
    gtc_date: datetime = None
    price: Decimal = None
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

    @classmethod
    def from_dict(cls, input_dict: dict):
        """
        Parses an Order object from an order dict.

        ...as of 4/17/2021...
        {
        'id': abc,
        'account-number':'abc123',
        'time-in-force': 'GTC',
        'order-type': 'Limit',
        'size': 1,
        'underlying-symbol': 'SPY',
        'underlying-instrument-type': 'Equity',
        'price': '0.94',
        'price-effect': 'Debit',
        'status': 'Received',
        'cancellable': True,
        'editable': True,
        'edited': False,
        'ext-exchange-order-number': '123',
        'ext-client-order-id': '123',
        'ext-global-order-number': 123,
        'received-at': '2021-04-06T17:06:38.904+00:00',
        'updated-at': 1618604409279,
        'legs': [{
                'instrument-type': 'Equity Option',
                'symbol': 'SPY   210716P00320000',
                'quantity': 1,
                'remaining-quantity': 1,
                'action': 'Buy to Close',
                'fills': []
                }]
        }
        """
        details = OrderDetails(input_dict['underlying-symbol'])
        details.id = input_dict.get('id')
        details.account = input_dict.get('account-number')
        details.time_in_force = input_dict.get('time-in-force')
        details.type = OrderType(input_dict['order-type'])
        details.size = input_dict.get('size')
        details.underlying = input_dict.get('underlying-symbol')
        details.price = Decimal(input_dict['price']) if 'price' in input_dict else None
        details.price_effect = OrderPriceEffect(input_dict['price-effect'])
        details.status = OrderStatus(input_dict['status'])
        details.received_at = datetime.strptime(input_dict.get('received-at'), '%Y-%m-%dT%H:%M:%S.%f%z')
        details.gtc_date = input_dict.get('gtc-date', None)
        details.legs = input_dict.get('legs', None)
        return cls(order_details=details)

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
