import datetime
import logging

import requests

LOGGER = logging.getLogger(__name__)


class TastyAPISession(object):
    def __init__(self, username: str, password: str, API_url=None):
        self.API_url = API_url if API_url else 'https://api.tastyworks.com'
        self.username = username
        self.password = password
        self.logged_in = False
        self.session_token = self._get_session_token()

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
        self._validate_session()
        return self.session_token

    def is_active(self):
        return self._validate_session()

    def _validate_session(self):
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
