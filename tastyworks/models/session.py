import asyncio
import datetime
import logging

import aiohttp
import requests

from tastyworks.models.trading_account import TradingAccount
from tastyworks.models.order import Order, OrderStatus


LOGGER = logging.getLogger(__name__)


class TastyAPISession(object):
    def __init__(self, username: str, password: str, API_url=None):
        self.API_url = API_url if API_url else 'https://api.tastyworks.com'
        self.username = username
        self.password = password
        self.logged_in = False
        self.session_token = self._get_session_token()
        self.accounts = None
        self._orders = None
        self.streamers = None

        # do setup functions here
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_init())

    async def _async_init(self):
        self.accounts = await self._get_trading_accounts()

    async def get_active_orders(self):
        return await self._get_remote_orders(status=OrderStatus.RECEIVED)

    async def _get_remote_orders(self, account_number=None, **kwargs):
        if account_number and account_number not in self.accounts:
            raise Exception('Could not find specified account number')
        res = {}
        for acct_number, acct in self.accounts.items():
            if account_number and acct_number != account_number:
                continue
            res[acct_number] = []
            orders = await Order.get_remote_orders(self, acct, **kwargs)
            res[acct_number] = res[acct_number] + orders
        return res

    def _get_session_token(self):
        if self.logged_in and self.session_token:
            if (datetime.datetime.now() - self.logged_in_at).total_seconds() < 60:
                return self.session_token

        body = {
            'login': self.username,
            'password': self.password
        }
        resp = requests.post(f'{self.API_url}/sessions', json=body)
        if resp.status_code != 201:
            self.logged_in = False
            self.logged_in_at = None
            self.session_token = None
            raise Exception('Failed to log in, message: {}'.format(resp.json()['error']['message']))

        self.logged_in = True
        self.logged_in_at = datetime.datetime.now()
        self.session_token = resp.json()['data']['session-token']
        self._validate_session(self.session_token)
        return self.session_token

    async def get_option_chains(self, symbol: str) -> dict:
        # NOTE: This guy may probably need to get refactored out into a sub-class of this one
        # For now, this just returns dxFeed-compatible option names
        async with aiohttp.request(
            'GET',
            f'{self.API_url}/option-chains/{symbol}/nested',
            headers=self.get_request_headers()
        ) as response:
            if response.status != 200:
                raise Exception(f'Could not find option chain for symbol {symbol}')
            resp = await response.json()
        res = {}
        data = resp['data']['items'][0]
        for exp in data['expirations']:
            exp_date = datetime.datetime.strptime(exp['expiration-date'], '%Y-%m-%d')
            exp_date_str = exp_date.strftime('%y%m%d')
            res[exp_date] = {}
            for strike in exp['strikes']:
                strike_val = float(strike['strike-price'])

                # remove .0 since dxFeed isn't happy about it
                if strike_val.is_integer():
                    strike_str = '{0:.0f}'.format(int(strike_val))
                else:
                    strike_str = '{0:.2f}'.format(strike_val)
                    if strike_str[-1] == '0':
                        strike_str = strike_str[:-1]

                item = {
                    'call': f'{symbol}{exp_date_str}C{strike_str}',
                    'put': f'{symbol}{exp_date_str}P{strike_str}'
                }
                res[exp_date][strike_val] = item
        return res

    def session_valid(self):
        return self._validate_session(self.session_token)

    async def _get_trading_accounts(self):
        accounts = {}
        url = f'{self.API_url}/customers/me/accounts'

        async with aiohttp.request('GET', url, headers=self.get_request_headers()) as response:
            if response.status != 200:
                raise Exception('Could not get trading accounts info from Tastyworks...')
            data = (await response.json())['data']

        for entry in data['items']:
            if entry['authority-level'] != 'owner':
                continue
            acct_data = entry['account']
            acct = TradingAccount(
                acct_data['account-number'],
                acct_data['external-id'],
                acct_data['margin-or-cash'] == 'Margin'
            )
            accounts[acct.account_number] = acct
        return accounts

    def get_trading_account_by_id(self, acct_id):
        return self.accounts[acct_id]

    def _validate_session(self, session_token):
        resp = requests.post(f'{self.API_url}/sessions/validate', headers=self.get_request_headers())
        if resp.status_code != 201:
            self.logged_in = False
            self.logged_in_at = None
            self.session_token = None
            raise Exception('Could not validate the session, error message: {}'.format(
                resp.json()['error']['message']
            ))
            return False
        return True

    def get_request_headers(self):
        return {
            'Authorization': self.session_token
        }
