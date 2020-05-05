from typing import List

import aiohttp
from dataclasses import dataclass

from tastyworks.models.order import Order, OrderPriceEffect, OrderType
from tastyworks.models.alert import Alert
from tastyworks.models.position import Position


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

    async def get_balance(session, account):
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

    async def get_quote_alert(session):
        """
        Get quote alerts.

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.
            account (TradingAccount): The account_id to get balance on.
        Returns:
            dict: quote alerts
        """
        url = '{}/quote-alerts'.format(session.API_url)

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception('Could not get quote alerts from Tastyworks...')
            data = Alert.from_dict((await response.json())['data']['items'])
        return data

    async def set_quote_alert(session, alert: Alert):
        """
        Create a quote alert.

        Args:
            alert (Alert): The Alert object to create.
            session (TastyAPISession): The tastyworks session onto which to execute the order.

        Returns:
            bool: Whether the alert creation was successful.
        """

        if not session.is_active():
            raise Exception('The supplied session is not active and valid')

        url = '{}/quote-alerts'.format(session.API_url)

        body = alert.get_json()

        async with aiohttp.request('POST', url, headers=session.get_request_headers(), json=body) as resp:
            if resp.status == 201:
                return True
            elif resp.status == 400:
                raise Exception('Failed to create the alert, message: {}'.format(await resp.text()))
            else:
                raise Exception('Unknown remote error, status code: {}, message: {}'.format(resp.status, await resp.text()))

    async def delete_quote_alert(session, alert: Alert):
        """
        Delete a quote alert.

        Args:
            alert (Alert): The Alert object to delete.  This must have the alert_external_id field set.
            session (TastyAPISession): The tastyworks session onto which to execute the order.

        Returns:
            bool: Whether the alert creation was successful.
        """

        if not session.is_active():
            raise Exception('The supplied session is not active and valid')

        if alert.alert_external_id == '':
            raise Exception('The supplied alert object does not have the alert_external_id value set.')

        url = '{}/quote-alerts/{}'.format(session.API_url, alert.alert_external_id)

        body = alert.get_json()

        async with aiohttp.request('DELETE', url, headers=session.get_request_headers(), json=body) as resp:
            if resp.status == 204:
                return True
            elif resp.status == 400:
                raise Exception('Failed to delete the quote alert, message: {}'.format(await resp.text()))
            else:
                raise Exception('Unknown remote error, status code: {}, message: {}'.format(resp.status, await resp.text()))

    async def get_positions(session, account):
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
            data = Position.list_from_dict((await response.json())['data']['items'])
        return data

    async def get_live_orders(session, account):
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

    async def get_history(session, account):
        """
        Get live Orders.

        Args:
            session (TastyAPISession): An active and logged-in session object against which to query.
            account (TradingAccount): The account_id to get history on.
        Returns:
            dict: account attributes
        """
        url = '{}/accounts/{}/transactions'.format(
            session.API_url,
            account.account_number
        )

        async with aiohttp.request('GET', url, headers=session.get_request_headers()) as response:
            if response.status != 200:
                raise Exception('Could not get history info from Tastyworks...')
            data = (await response.json())['data']
        return data


def _get_execute_order_json(order: Order):
    order_json = {
        'source': order.details.source,
        'order-type': order.details.type.value,
        'price-effect': order.details.price_effect.value,
        'time-in-force': order.details.time_in_force.value,
        'legs': _get_legs_request_data(order)
    }

    if order.details.type == OrderType.STOP_LIMIT or order.details.type == OrderType.STOP:
        order_json['stop-trigger'] = '{:.2f}'.format(order.details.stop_trigger)

    if not order.details.type == OrderType.STOP and not order.details.type == OrderType.MARKET:
        order_json['price'] = '{:.2f}'.format(order.details.price)

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
