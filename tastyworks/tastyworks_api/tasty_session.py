import aiohttp
import datetime
import logging

import requests

LOGGER = logging.getLogger(__name__)

# TODO:
# * Implement get option chains


class TastyAPISession(object):
    def __init__(self, username: str, password: str, API_url=None):
        self.API_url = API_url if API_url else 'https://api.tastyworks.com'
        self.username = username
        self.password = password
        self.logged_in = False
        self.session_token = self.get_session_token()

    def get_session_token(self):
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
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.API_url}/option-chains/{symbol}/nested', headers=self._get_request_headers()) as response:
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

    def _validate_session(self, session_token):
        resp = requests.post(f'{self.API_url}/sessions/validate', headers=self._get_request_headers())
        if resp.status_code != 201:
            self.logged_in = False
            self.logged_in_at = None
            self.session_token = None
            raise Exception('Could not validate the session, error message: {}'.format(
                resp.json()['error']['message']
            ))
            return False
        return True

    def get_streamer_token(self):
        return self._get_streamer_data()['data']['token']

    def get_streamer_websocket_url(self):
        socket_url = self._get_streamer_data()['data']['websocket-url']
        socket_url = socket_url.replace('https://', '')
        full_url = 'wss://{}/cometd'.format(socket_url)
        return full_url

    def _get_request_headers(self):
        return {
            'Authorization': self.session_token
        }

    def _get_streamer_data(self):
        if not self.logged_in:
            raise Exception('Logged in session required')

        if hasattr(self, 'streamer_data_created') and (datetime.datetime.now() - self.streamer_data_created).total_seconds() < 60:
            return self.streamer_data

        resp = requests.get(f'{self.API_url}/quote-streamer-tokens', headers=self._get_request_headers())
        if resp.status_code != 200:
            raise Exception('Could not get quote streamer data, error message: {}'.format(
                resp.json()['error']['message']
            ))
        self.streamer_data = resp.json()
        self.streamer_data_created = datetime.datetime.now()
        return resp.json()
