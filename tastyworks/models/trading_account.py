from typing import List

import aiohttp
from dataclasses import dataclass

from tastyworks.models.order import Order, OrderPriceEffect
from tastyworks.models.session import TastyAPISession


@dataclass
class TradingAccount(object):
    account_number: str
    external_id: str
    is_margin: bool
    session: TastyAPISession

    async def execute_order(self, order: Order, dry_run=True):
        """
        Execute an order. If doing a dry run, the order isn't placed but simulated (server-side).

        Args:
            order (Order): The order object to execute.
            dry_run (bool): Whether to do a test (dry) run.

        Returns:
            bool: Whether the order was successful.
        """
        if not order.check_is_order_executable():
            raise Exception('Order is not executable, most likely due to missing data')

        if not self.session.is_active():
            raise Exception('The session is not active or valid')

        url = '{}/accounts/{}/orders'.format(
            self.session.API_url,
            self.account_number
        )
        if dry_run:
            url = f'{url}/dry-run'

        body = _get_execute_order_json(order)

        async with aiohttp.request('POST', url, headers=self.session.get_request_headers(), json=body) as resp:
            if resp.status == 201:
                return True
            elif resp.status == 400:
                raise Exception('Order execution failed, message: {}'.format(await resp.text()))
            else:
                raise Exception('Unknown remote error, status code: {}, message: {}'.format(resp.status, await resp.text()))

    @classmethod
    def from_dict(cls, data: dict, session: TastyAPISession) -> List:
        """
        Parses a TradingAccount object from a dict.
        """
        new_data = {
            'is_margin': True if data['margin-or-cash'] == 'Margin' else False,
            'account_number': data['account-number'],
            'external_id': data['external-id'],
            'session': session
        }

        res = TradingAccount(**new_data)

        return res

    @classmethod
    async def get_accounts(cls, session) -> List:
        """
        Gets all trading accounts from the Tastyworks platform.

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.

        Returns:
            list (TradingAccount): A list of trading accounts.
        """
        url = f'{session.API_url}/customers/me/accounts'
        res = []

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception(f'HTTP {response.status} during GET accounts')
            data = (await response.json())['data']

        for entry in data['items']:
            if entry['authority-level'] != 'owner':
                continue
            acct_data = entry['account']
            acct = TradingAccount.from_dict(acct_data, session)
            res.append(acct)

        return res

    async def get_balance(self):
        """
        Get balance.

        Args:
            account (TradingAccount): The account to get balance on.
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/balances'.format(
            self.session.API_url,
            self.account_number
        )

        async with aiohttp.request('GET', url, headers=self.session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception(f'HTTP {response.status} during GET balances from {self.account_number}')
            data = (await response.json())['data']
        return data

    async def get_positions(self):
        """
        Get Open Positions.

        Args:
            account (TradingAccount): The account to get positions on.
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/positions'.format(
            self.session.API_url,
            self.account_number
        )

        async with aiohttp.request('GET', url, headers=self.session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception(f'HTTP {response.status} during GET positions from {self.account_number}')
            data = (await response.json())['data']['items']
        return data

    async def get_live_orders(self):
        """
        Get live orders from the account

        Args:
            None
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/orders/live'.format(
            self.session.API_url,
            self.account_number
        )

        async with aiohttp.request('GET', url, headers=self.session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception(f'HTTP {response.status} during GET orders/live')
            data = (await response.json())['data']['items']
        return data

    async def get_history(self):
        """
        Get transaction history from the account

        Args:
            None
        Returns:
            dict: account attributes
        """
        total_pages = page = 0
        history = []
        while True:
            url = '{}/accounts/{}/transactions?start-at=2020-01-01&end-at=2022-12-31&per-page=100&page-offset={}'.format(
                self.session.API_url,
                self.account_number,
                page
            )
            async with aiohttp.request('GET', url, headers=self.session.get_request_headers()) as response:
                if response.status != 200:
                    raise Exception(f'HTTP {response.status} during GET transactions')
                tmp = (await response.json())
                if 'pagination' in tmp.keys():
                    total_pages = tmp['pagination']['total-pages']
                history.extend(tmp['data']['items'])
            page += 1
            if page == total_pages:
                break
        return history


def _get_execute_order_json(order: Order):
    order_json = {
        'source': order.details.source,
        'order-type': order.details.type.value,
        'price': '{:.2f}'.format(order.details.price),
        'price-effect': order.details.price_effect.value,
        'time-in-force': order.details.time_in_force.value,
        'legs': _get_legs_request_data(order)
    }

    if order.details.gtc_date:
        order_json['gtc-date'] = order.details.gtc_date.strftime('%Y-%m-%d')

    return order_json


def _get_legs_request_data(order):
    res = []
    order_effect = order.details.price_effect
    order_effect_str = 'Sell to Open' if order_effect == OrderPriceEffect.CREDIT else 'Buy to Open'
    for leg in order.details.legs:
        leg_dict = {**leg.to_tasty_json(), 'action': order_effect_str}
        res.append(leg_dict)
    return res
