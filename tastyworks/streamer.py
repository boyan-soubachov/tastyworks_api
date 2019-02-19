import asyncio
import datetime
import json
import logging

import aiocometd
import requests

from tastyworks.dxfeed import mapper as dxfeed_mapper
from tastyworks.models.session import TastyAPISession

LOGGER = logging.getLogger(__name__)


# TODO:
# * Proper exception handling and bubbling

class DataStreamer(object):
    def __init__(self, session: TastyAPISession):
        if not session.is_active():
            raise Exception('TastyWorks API session not active/valid')
        self.tasty_session = session
        self.cometd_client = None
        self.subs = {}
        asyncio.get_event_loop().run_until_complete(
            self._setup_connection()
        )

    def __del__(self):
        asyncio.get_event_loop().run_until_complete(
            self.cometd_client.close()
        )

    async def _cometd_close(self):
        await self.cometd_client.close()

    async def add_data_sub(self, values):
        LOGGER.debug(f'Adding subscription: {values}')
        await self._send_msg('/service/sub', {'add': values})

    async def remove_data_sub(self, values):
        # NOTE: Experimental, unconfirmed. Needs testing
        LOGGER.info(f'Removing subscription: {values}')
        await self._send_msg('/service/sub', {'remove': values})

    async def _consumer(self, message):
        msg_object = json.loads(message)
        LOGGER.debug('Object conversion: %s', msg_object)
        return dxfeed_mapper.map_message(msg_object)

    async def _send_msg(self, channel, message):
        if not self.logged_in:
            raise Exception('Connection not made or logged in')
        LOGGER.debug('[dxFeed] sending: %s', message)
        await self.cometd_client.publish(channel, message)

    async def reset_data_subs(self):
        LOGGER.info('Resetting data subscriptions')
        await self._send_msg('/service/sub', {'reset': True})

    def get_streamer_token(self):
        return self._get_streamer_data()['data']['token']

    def _get_streamer_data(self):
        if not self.tasty_session.logged_in:
            raise Exception('Logged in session required')

        if hasattr(self, 'streamer_data_created') and (datetime.datetime.now() - self.streamer_data_created).total_seconds() < 60:
            return self.streamer_data

        resp = requests.get(f'{self.tasty_session.API_url}/quote-streamer-tokens', headers=self.tasty_session.get_request_headers())
        if resp.status_code != 200:
            raise Exception('Could not get quote streamer data, error message: {}'.format(
                resp.json()['error']['message']
            ))
        self.streamer_data = resp.json()
        self.streamer_data_created = datetime.datetime.now()
        return resp.json()

    def _get_streamer_websocket_url(self):
        socket_url = self._get_streamer_data()['data']['websocket-url']
        socket_url = socket_url.replace('https://', '')
        full_url = 'wss://{}/cometd'.format(socket_url)
        return full_url

    async def _setup_connection(self):
        streamer_url = self._get_streamer_websocket_url()
        LOGGER.info('Connecting to url: %s', streamer_url)

        auth_extension = AuthExtension(self.get_streamer_token())
        cometd_client = aiocometd.Client(
            streamer_url,
            auth=auth_extension,
            connection_types=aiocometd.ConnectionType.WEBSOCKET
        )
        await cometd_client.open()

        self.cometd_client = cometd_client
        self.logged_in = True
        LOGGER.info('Connected and logged in to dxFeed data stream')

        # await self.reset_data_subs()

        LOGGER.info('Connection setup completed!')

    async def listen(self):
        async for msg in self.cometd_client:
            LOGGER.debug('[dxFeed] received: %s', msg)
            res = await self._consumer(msg)
            if not res:
                continue
            yield res


class AuthExtension(aiocometd.AuthExtension):
    def __init__(self, streamer_token: str):
        self.streamer_token = streamer_token

    def _get_login_msg(self):
        return {'ext': {'com.devexperts.auth.AuthToken': f'{self.streamer_token}'}}

    def _get_advice_msg(self):
        return {
            'timeout': 60 * 1000,
            'interval': 0
        }

    async def incoming(self, payload, headers=None):
        pass

    async def outgoing(self, payload, headers=None):
        for entry in payload:
            if 'clientId' not in entry:
                entry.update(self._get_login_msg())

    async def authenticate(self):
        pass
