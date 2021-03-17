from typing import List

import aiohttp
from dataclasses import dataclass

from tastyworks.models.order import Order, OrderPriceEffect


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
            session (TastyAPISession): The tastyworks session onto which to execute the order.
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

        body = _get_execute_order_json(order)

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

    async def get_balance(self, session, account):
        """
        Get balance.

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.
            account (TradingAccount): The account_id to get balance on.
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/balances'.format(
            session.API_url,
            account.account_number
        )

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception('Could not get trading account balance info from Tastyworks...')
            data = (await response.json())['data']
        return data

    async def get_positions(self, session, account):
        """
        Get Open Positions.

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.
            account (TradingAccount): The account_id to get positions on.
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/positions'.format(
            session.API_url,
            account.account_number
        )

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception('Could not get open positions info from Tastyworks...')
            data = (await response.json())['data']['items']
        return data

    async def get_live_orders(self, session, account):
        """
        Get live Orders.

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.
            account (TradingAccount): The account_id to get live orders on.
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/orders/live'.format(
            session.API_url,
            account.account_number
        )

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception('Could not get live orders info from Tastyworks...')
            data = (await response.json())['data']['items']
        return data

    async def get_history(self, session, start_at: str = None, 
        end_at: str = None, per_page: int = None, page_offset: int = 0
    ):
        """Get Transaction History

        Warning for Windows users:
            This will likely throw OSError: [WinError 10038] ...
            It doesn't seem to effect the actual event loop, however, it is recommended that
            you define the event loop policy for asyncio if you want to ensure quality before
            retrieving the event loop.

            Example:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            loop = asyncio.get_event_loop()

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.
            start_at (str): DD-MM-YYYY
            end_at (str): DD-MM-YYYY
            per_page (int): # of items for the API to return per page
            page_offset (int): Page # to start with

        Returns:
            dict: Account transaction history
        """

        total_pages = page = 0
        history = []
        params = {"page-offset": page_offset}

        # Ensure we don't pass None to aiohttp.request
        if start_at is not None:
            params["start-at"] = start_at
        if end_at is not None:
            params["end-at"] = end_at
        if per_page is not None:
            params["per-page"] = per_page

        url = '{}/accounts/{}/transactions'.format(
            session.API_url,
            self.account_number
        )
        

        while params["page-offset"] <= total_pages:
            url = '{}/accounts/{}/transactions'.format(
                session.API_url,
                self.account_number
            )

            async with aiohttp.request('GET', url, headers=session.get_request_headers(), params=params) as response:
                if response.status != 200:
                    raise Exception(
                        f'Failed retrieving transaction history, Response status: {response.status}; message: {response.json()["error"]["message"]}'
                    )

                current_page = await response.json()
                history.extend(current_page["data"]["items"])

                if not total_pages and 'pagination' in current_page.keys():
                    total_pages = current_page["pagination"]["total-pages"]

            params["page-offset"] += 1

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
