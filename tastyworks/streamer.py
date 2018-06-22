import asyncio
import json
import logging
import threading

import websockets

from tastyworks.dxfeed import mapper as dxfeed_mapper
from tastyworks.tastyworks_api.tasty_session import TastyAPISession

LOGGER = logging.getLogger(__name__)


# TODO:
# * Proper exception handling and bubbling
# * Figure out how to remove stream subscriptions

class DataStreamer(object):
    def __init__(self, tasty_session: TastyAPISession, timeout=60):
        # initiate with a tasty session object
        if not tasty_session.session_valid():
            raise Exception('TastyWorks API session not valid')
        self.tasty_api_session = tasty_session
        self.timeout = timeout
        self.connection = None
        self.logged_in = False
        self.subs = {}
        self.lock = asyncio.Lock()
        asyncio.get_event_loop().run_until_complete(
            self._setup_connection()
        )

    def get_tasty_session(self):
        if not self.tasty_api_session:
            raise Exception('No active tastyworks API session attached to streamer, critical error!')
        return self.tasty_api_session

    def __del__(self):
        self.ka_thread.join()  # Kill the keep-alive thread
        self.connection.close()

    def _get_nonce(self):
        # NOTE: It seems a mutex is not necessary as long as we
        # have no replay of messages (i.e. do not send with same/lower number)
        if not hasattr(self, 'nonce'):
            self.nonce = 1
        else:
            self.nonce = self.nonce + 1

        return self.nonce

    async def add_data_sub(self, values):
        LOGGER.debug(f'Adding subscription: {values}')
        # TODO: fragment message if need be, max 64k
        message = [
            {
                'channel': '/service/sub',
                'clientId': self.client_id,
                'id': self._get_nonce(),
                'data': {
                    'add': values
                }
            }
        ]

        await self._send_msg(message)

    async def remove_data_sub(self, values):
        # NOTE: Experimental, unconfirmed. Needs testing
        LOGGER.info(f'Removing subscription: {values}')
        message = [
            {
                'channel': '/service/sub',
                'clientId': self.client_id,
                'id': self._get_nonce(),
                'data': {
                    'remove': values
                }
            }
        ]
        await self._send_msg(message)

    def _get_login_msg(self) -> str:
        auth_token = self.tasty_api_session.get_streamer_token()
        return json.dumps([{
            'ext': {
                'com.devexperts.auth.AuthToken': f'{auth_token}'
            },
            'id': self._get_nonce(),
            'version': '1.0',
            'minimumVersion': '1.0',
            'channel': '/meta/handshake',
            'supportedConnectionTypes': [
                'websocket',
                'long-polling',
                'callback-polling'
            ],
            'advice': {
                'timeout': self.timeout * 1000,
                'interval': 0
            }
        }])

    def _get_connect_msg(self, advice=True) -> str:
        if advice:
            msg = [
                {
                    "advice": {
                        "timeout": 0
                    },
                    "channel": "/meta/connect",
                    "clientId": self.client_id,
                    "connectionType": "websocket",
                    "id": self._get_nonce()
                }
            ]
        else:
            msg = [
                {
                    "channel": "/meta/connect",
                    "clientId": self.client_id,
                    "connectionType": "websocket",
                    "id": self._get_nonce()
                }
            ]
        return msg

    async def _consumer(self, message):
        msg_object = json.loads(message)
        LOGGER.debug('Object conversion: %s', msg_object)
        return dxfeed_mapper.map_message(msg_object)

    async def _send_msg(self, message):
        if not self.logged_in:
            raise Exception('Connection not made and logged in')
        if not isinstance(message, str):
            message = json.dumps(message)
        LOGGER.debug('[dxFeed] sending: %s', message)
        await self.connection.send(message)

    async def reset_data_subs(self):
        LOGGER.info('Resetting data subscriptions')
        msg = [
            {
                "channel": "/service/sub",
                "clientId": self.client_id,
                "data": {
                    "reset": True
                },
                "id": self._get_nonce()
            }
        ]
        await self._send_msg(msg)
        await self.connection.recv()

    async def _setup_connection(self):
        streamer_url = self.tasty_api_session.get_streamer_websocket_url()
        logging.info('Connecting to url: %s', streamer_url)
        socket = await websockets.connect(streamer_url)
        # login
        LOGGER.debug('Sending login message: %s', self._get_login_msg())
        await socket.send(self._get_login_msg())
        login_resp = json.loads(await socket.recv())
        login_resp = login_resp[0]
        advised_timeout = login_resp['advice']['timeout']
        LOGGER.debug('Received login response: %s', login_resp)
        if not login_resp['successful']:
            raise Exception('Could not login to dxFeed stream')
        self.client_id = login_resp['clientId']
        self.connection = socket
        self.logged_in = True
        LOGGER.info('Connected and logged in to dxFeed data stream')
        await self.reset_data_subs()
        # connect
        await self._send_msg(self._get_connect_msg())
        await socket.recv()

        # set up advice-based keep-alives/pings
        loop = asyncio.get_event_loop()
        self.ka_thread = threading.Thread(
            target=self._set_ka_loop,
            args=(loop, advised_timeout),
            daemon=True
        )
        self.ka_thread.start()

        LOGGER.info('Connection setup completed!')

    def _set_ka_loop(self, loop, period):
        LOGGER.info('Starting keep-alive thread with period: %s ms', period)
        asyncio.run_coroutine_threadsafe(self._keep_alive(period), loop)

    async def _keep_alive(self, period: int):
        """
        Handles the keep-alive message.

        Args:
            period: The time period, must be in milliseconds.
        """
        while True:
            LOGGER.debug('Sending keep-alive message')
            await self._send_msg(self._get_connect_msg(advice=False))
            await asyncio.sleep(period / 1000)

    async def listen(self):
        async for msg in self.connection:
            LOGGER.debug('[dxFeed] received: %s', msg)
            res = await self._consumer(msg)
            if not res:
                continue
            yield res
