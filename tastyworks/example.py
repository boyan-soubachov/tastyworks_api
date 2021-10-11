import asyncio
import calendar
import logging
import os
from datetime import date, timedelta

import aiohttp
from tastyworks.models import option_chain, underlying
from tastyworks.models.order import (Order)
from tastyworks.models.session import TastyAPISession
from tastyworks.models.trading_account import TradingAccount
from tastyworks.models.underlying import Underlying

from tastyworks.streamer import DataStreamer
from tastyworks.tastyworks_api import tasty_session

LOGGER = logging.getLogger(__name__)


async def get_watchlists(session):
    async with aiohttp.request(
            'GET',
            f'{session.API_url}/public-watchlists',
            headers=session.get_request_headers()) as response:
        if response.status != 200:
            raise Exception(f'Could not get watchlists')
        resp = await response.json()

        return resp['data']['items']


async def _get_tasty_market_metrics(session, underlying):
    async with aiohttp.request(
            'GET',
            f'{session.API_url}/market-metrics?symbols={underlying.ticker}',
            headers=session.get_request_headers()) as response:
        if response.status != 200:
            raise Exception(f'Could not market metrics for symbol {underlying.ticker}')
        resp = await response.json()

        return resp['data']['items'][0]


async def get_market_metrics(session, underlying: Underlying, expiration: date = None):
    LOGGER.debug('Getting market metrics for ticker: %s', underlying.ticker)
    data = await _get_tasty_market_metrics(session, underlying)
    res = data
    return res


async def main_loop(session: TastyAPISession, streamer: DataStreamer):
    # sub_values = {
    #     "Greeks": [
    #         ".VIX180718C21",
    #         ".YUM180518C95"
    #     ]
    # }
    sub_values = {
        "Quote": ["/ES"]
    }

    accounts = await TradingAccount.get_remote_accounts(session)
    acct = accounts[0]
    LOGGER.info('Accounts available: %s', accounts)

    orders = await Order.get_remote_orders(session, acct)
    LOGGER.info('Number of active orders: %s', len(orders))

    # Execute an order

    details = OrderDetails(
        type=OrderType.LIMIT,
        price=Decimal(400),
        price_effect=OrderPriceEffect.CREDIT)
    new_order = Order(details)

    opt = Option(
        ticker='AKS',
        quantity=1,
        expiry=get_third_friday(date.today()),
        strike=Decimal(3),
        option_type=OptionType.CALL,
        underlying_type=UnderlyingType.EQUITY
    )
    new_order.add_leg(opt)

    res = await acct.execute_order(new_order, session, dry_run=True)
    LOGGER.info('Order executed successfully: %s', res)

    # Get an options chain
    undl = underlying.Underlying('AKS')

    chain = await option_chain.get_option_chain(session, undl)
    LOGGER.info('Chain strikes: %s', chain.get_all_strikes())

    market_metrics = await get_market_metrics(session, undl)
    LOGGER.info('market metrics: %s', market_metrics)

    watchlists = await get_watchlists(session)
    LOGGER.info('watchlists', watchlists)

    await streamer.add_data_sub(sub_values)

    async for item in streamer.listen():
        LOGGER.info('Received item: %s' % item.data)


def get_third_friday(d):
    s = date(d.year, d.month, 15)
    candidate = s + timedelta(days=(calendar.FRIDAY - s.weekday()) % 7)

    # This month's third friday passed
    if candidate < d:
        candidate += timedelta(weeks=4)
        if candidate.day < 15:
            candidate += timedelta(weeks=1)

    return candidate


def main():
    tasty_client = tasty_session.create_new_session(environ.get('TW_USER', ""),
                                                    environ.get('TW_PASSWORD', ""))

    streamer = DataStreamer(tasty_client)
    LOGGER.info('Streamer token: %s' % streamer.get_streamer_token())
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_loop(tasty_client, streamer))
    except Exception:
        LOGGER.exception('Exception in main loop')
    finally:
        # find all futures/tasks still running and wait for them to finish
        pending_tasks = [
            task for task in asyncio.Task.all_tasks() if not task.done()
        ]
        loop.run_until_complete(asyncio.gather(*pending_tasks))
        loop.close()


if __name__ == '__main__':
    main()
