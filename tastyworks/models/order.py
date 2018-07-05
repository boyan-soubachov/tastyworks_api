import logging
from enum import Enum
from typing import List

import aiohttp

from tastyworks.models.model import Model

LOGGER = logging.getLogger(__name__)


class OrderType(Enum):
    LIMIT = 'Limit'
    MARKET = 'Market'


class OrderEffect(Enum):
    CREDIT = 'Credit'
    DEBIT = 'Debit'


class OrderStatus(Enum):
    RECEIVED = 'Received'
    CANCELLED = 'Cancelled'
    FILLED = 'Filled'
    EXPIRED = 'Expired'


class Order(Model):
    def __init__(self, account, price, price_effect, **kwargs):
        """
        Initiates a new order object.

        Args:
            account (TradingAccount): The trading account to execute on.
            type (OrderType): The type of order to make.
            price (float): The order price level (this is total, sum of all legs).
            price_effect (OrderEffect): Whether this is a credit or debit order.
            session
        """
        self.id = kwargs['order_id'] if 'order_id' in kwargs else None
        self.type = kwargs['type'] if 'type' in kwargs else OrderType.LIMIT
        self.time_in_force = kwargs['time_in_force'] if 'time_in_force' in kwargs else "Day"
        self.price = price
        self.price_effect = price_effect
        self.status = kwargs['status'] if 'status' in kwargs else None
        self.account = account
        self.session = None
        self.legs = []
        self.quantity = kwargs['quantity'] if 'quantity' in kwargs else 0

    async def execute(self, dry_run=True):
        """
        Execute an order. If doing a dry run, the order isn't placed but simulated (server-side).

        Args:
            dry_run (bool): Whether to do a test (dry) run.

        Returns:
            bool: Whether the order was successful.
            dict: Information about the order.
        """
        if not self.account:
            raise Exception('Cannot execute an order without active trading accounts')

        if not self.session.logged_in:
            raise Exception('Cannot execute an order without a connected session')

        url = '{}/accounts/{}/orders'.format(
            self.session.API_url,
            self.account.account_number
        )
        if dry_run:
            url = f'{url}/dry-run'

        # TODO: Complete this. We need to add models for order legs (aka option legs).
        body = {
            'source': 'WBT',
            'order-type': self.type.value,
            'price': str(self.price),
            'price-effect': self.price_effect.value,
            'time-in-force': self.time_in_force.value,
            'legs': {}  # TODO: ...
        }

        async with aiohttp.request('POST', url, headers=self.session.get_request_headers(), body=body) as resp:
            if resp.status not in (200, 201):
                raise Exception('Could not execute a trade order successfully')
            data = await resp.json()
            self.status = OrderStatus(data['data']['order']['status'])

            if self.status == OrderStatus.RECEIVED:
                success = True
            else:
                success = False

            return success, data

    @classmethod
    def from_dict(cls, session, account, input_dict: dict):
        """
        Parses an Order object from a dict.
        """
        return cls(
            account=account,
            price=float(input_dict['price']),
            price_effect=OrderEffect(input_dict['price-effect']),
            type=OrderType(input_dict['order-type']),
            status=OrderStatus(input_dict['status']),
            order_id=input_dict['id'],
            time_in_force=input_dict['time-in-force']
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

        filters = kwargs or {
            'status': OrderStatus.RECEIVED.value
        }
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
                order = cls.from_dict(session, account, order_data)
                res.append(order)
        return res
