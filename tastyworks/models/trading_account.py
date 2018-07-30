from typing import List

import aiohttp
from dataclasses import dataclass

from tastyworks.models.order import Order


@dataclass
class TradingAccount(object):
    account_number: str
    external_id: str
    is_margin: bool

    async def execute_order(self, order: Order, session, dry_run=True):
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

        if not session.is_active():
            raise Exception('The supplied session is not active and valid')

        url = '{}/accounts/{}/orders'.format(
            session.API_url,
            self.account_number
        )
        if dry_run:
            url = f'{url}/dry-run'

        body = {
            'source': order.details.source,
            'order-type': order.details.type.value,
            'price': str(order.details.price),
            'price-effect': order.details.price_effect.value,
            'time-in-force': order.details.time_in_force,
            'legs': order.details.legs.asdict()
        }

        async with aiohttp.request('POST', url, headers=session.get_request_headers(), json=body) as resp:
            if resp.status == 201:
                return True
            elif resp.status == 400:
                raise Exception('Order execution failed, message: {}'.format(await resp.text()))
            else:
                raise Exception('Unknown remote error, status code: {}, message: {}'.format(resp.status, await resp.text()))

    @classmethod
    def from_dict(cls, data: dict) -> List:
        """
        Parses a TradingAccount object from a dict.
        """
        new_data = {
            'is_margin': True if data['margin-or-cash'] == 'Margin' else False,
            'account_number': data['account-number'],
            'external_id': data['external-id']
        }

        res = TradingAccount(**new_data)

        return res

    @classmethod
    async def get_remote_accounts(cls, session) -> List:
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
                raise Exception('Could not get trading accounts info from Tastyworks...')
            data = (await response.json())['data']

        for entry in data['items']:
            if entry['authority-level'] != 'owner':
                continue
            acct_data = entry['account']
            acct = TradingAccount.from_dict(acct_data)
            res.append(acct)

        return res
