import asyncio
import calendar
import logging
from os import environ
from datetime import date, timedelta
from decimal import Decimal

from tastyworks.models import option_chain, underlying
from tastyworks.models.option import Option, OptionType
from tastyworks.models.order import (Order, OrderDetails, OrderPriceEffect, OrderType)
from tastyworks.models.session import TastyAPISession
from tastyworks.models.trading_account import TradingAccount
from tastyworks.models.underlying import UnderlyingType
from tastyworks.streamer import DataStreamer
from tastyworks.tastyworks_api import tasty_session

LOGGER = logging.getLogger(__name__)


async def main_loop(session: TastyAPISession, streamer: DataStreamer):
    # sub_values = {
    #     "Greeks": [
    #         ".VIX180718C21",
    #         ".YUM180518C95"
    #     ]
    # }
    sub_values = {
        "Quote": ["SPY"]
    }

    # Get accounts
    accounts = await TradingAccount.get_remote_accounts(session)
    acct = accounts[1]
    LOGGER.info('Accounts available: %s', accounts)

    # Get open orders
    orders = await Order.get_remote_orders(session, acct)
    LOGGER.info('Number of active orders: %s', len(orders))

    # List all the open orders
    for order in orders:
        print(order.details)

    # # Execute an order
    # details = OrderDetails(
    #     type=OrderType.LIMIT,
    #     price=Decimal(400),
    #     price_effect=OrderPriceEffect.CREDIT)
    # new_order = Order(details)
    #
    # opt = Option(
    #     ticker='AKS',
    #     quantity=1,
    #     expiry=get_third_friday(date.today()),
    #     strike=Decimal(3),
    #     option_type=OptionType.CALL,
    #     underlying_type=UnderlyingType.EQUITY
    # )
    # new_order.add_leg(opt)
    #
    # res = await acct.execute_order(new_order, session, dry_run=True)
    # LOGGER.info('Order executed successfully: %s', res)

    # # Get an options chain
    # undl = underlying.Underlying('AKS')
    #
    # chain = await option_chain.get_option_chain(session, undl)
    # LOGGER.info('Chain strikes: %s', chain.get_all_strikes())

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
    """
    1. Get API auth token (Session) using Username & Password at 'https://api.tastyworks.com/sessions'
    2. Get a Streamer auth token with the API auth token at 'https://tasty-live-web.dxfeed.com/live'
    """
    # # Creating a new session fetching username and password in environment variable
    # # Username and Password should be set in permanent environment variables
    # print(environ.get('TW_USER', ""))
    # print(environ.get('TW_PASSWORD', ""))

    # /tastyworks/tastyworks_api/tasty_session.py
    LOGGER.info('Creating the API session...')
    tasty_client = tasty_session.create_new_session(environ.get('TW_USER', ""), environ.get('TW_PASSWORD', ""))

    # /tastyworks/streamer.py
    LOGGER.info('Creating DataStreamer session...')
    streamer = DataStreamer(tasty_client)
    LOGGER.info('Streamer token: %s' % streamer.get_streamer_token())

    loop = asyncio.get_event_loop()

    try:
        # Start main_loop()
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
