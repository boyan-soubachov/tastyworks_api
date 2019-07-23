import asyncio
import datetime
import json
import logging
import threading
from typing import List

import requests
import websockets

from tastyworks.models.session import TastyAPISession

LOGGER = logging.getLogger(__name__)


# TODO:
# * Proper exception handling and bubbling
# * Figure out how to remove stream subscriptions

class AccountStreamer(object):
    def __init__(self, session: TastyAPISession, timeout=5000):
        if not session.is_active():
            raise Exception('TastyWorks API session not active/valid')
        self.tasty_session = session
        self.timeout = timeout
        self.connection = None
        self.lock = asyncio.Lock()
        asyncio.get_event_loop().run_until_complete(
            self._setup_connection()
        )

    def __del__(self):
        self.ka_thread.join()  # Kill the keep-alive thread
        self.connection.close()

    async def add_account_sub(self, account_numbers):

        LOGGER.debug(f'Adding account subscribe: {account_numbers}')
  
        await self._send_msg(self._get_account_subscribe_msg(account_numbers))
        #await self.connection.recv()

    def __get_action_msg(self, action, value=None, request_id=None) -> List:
        msg = {
            "action": action,
            "request-id": request_id,
            "auth-token": self.tasty_session.session_token,
        }
        if value:
            msg["value"] = value

        return json.dumps(msg)

    def _get_account_subscribe_msg(self, accounts, request_id=None) -> List:
        return self.__get_action_msg('account-subscribe', accounts, request_id)

    def _get_heartbeat_msg(self) -> List:
        return self.__get_action_msg('heartbeat')

    async def _consumer(self, message):
        msg_object = json.loads(message)
        LOGGER.debug('Object conversion: %s', msg_object)
        return msg_object

    async def _send_msg(self, message):
        if not isinstance(message, str):
            message = json.dumps(message)
        LOGGER.debug('[acctFeed] sending: %s', message)
        await self.connection.send(message)
  
    def _get_streamer_websocket_url(self):
        return 'wss://streamer.tastyworks.com/'

    async def _setup_connection(self):
        streamer_url = self._get_streamer_websocket_url()
        LOGGER.info('Connecting to url: %s', streamer_url)
        socket = await websockets.connect(streamer_url)

        self.connection = socket

        LOGGER.info('Connected to Accounts data stream')

        # set up advice-based keep-alives/pings
        loop = asyncio.get_event_loop()
        self.ka_thread = threading.Thread(
            target=self._set_ka_loop,
            args=(loop, self.timeout),
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
            await self._send_msg(self._get_heartbeat_msg())
            await asyncio.sleep(period / 5000)

    async def listen(self):
        async for msg in self.connection:
            LOGGER.debug('[acctFeed] received: %s', msg)
            res = await self._consumer(msg)
            if not res:
                continue
            yield res
