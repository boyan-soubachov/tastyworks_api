import asyncio
import calendar
import logging

from os import environ
from datetime import date, timedelta
from decimal import Decimal

from tastyworks.models import option_chain, underlying
from tastyworks.models.option import Option, OptionType
from tastyworks.models.order import (Order, OrderDetails, OrderPriceEffect,
                                     OrderType)
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
        "Quote": ["/ES"]
    }

    accounts = await TradingAccount.get_accounts(session)
    account_nums = list(map(lambda x: x.account_number, accounts))
    print(f'Accounts available: {account_nums}')

    for acct in accounts:
        anum = acct.account_number
        bal = await acct.get_balance()
        print(f'--- Account {anum} Balances ---')
        print(bal)

        print(f'--- Account {anum} Positions ---')
        positions = await acct.get_positions()
        for pos in positions:
            print(f'{pos["symbol"]:30s} {pos["quantity"]:3d} {pos["average-open-price"]:8s} {pos["close-price"]}')

        print(f'--- Account {anum} Transaction History ---')
        history = await acct.get_history()
        for h in history:
            # print(f'{h["executed-at"]:20s} {h["action"]:15s} {h["underlying-symbol"]:6s} {h["quantity"]} {h["price"]}')
            print(f'{h["executed-at"]:32s} {h["description"]}')

    orders = await Order.get_remote_orders(session, acct)
    print(f'Number of active orders: {len(orders)}')

    await streamer.add_data_sub(sub_values)

    print('Monitoring /ES updates...')
    async for item in streamer.listen():
        LOGGER.info('Received item: %s' % item.data)


async def execute_order(acct, session):
    # Execute an order
    details = OrderDetails(
        type=OrderType.LIMIT,
        price=Decimal(400),
        price_effect=OrderPriceEffect.CREDIT)
    new_order = Order(details)

    opt = Option(
        ticker='F',
        quantity=1,
        expiry=get_third_friday(date.today()),
        strike=Decimal(3),
        option_type=OptionType.CALL,
        underlying_type=UnderlyingType.EQUITY
    )
    new_order.add_leg(opt)

    res = await acct.execute_order(new_order, session, dry_run=True)
    LOGGER.info('Order executed successfully: %s', res)


async def get_options_chain(symbol, session):
    # Get an options chain
    try:
        undl = underlying.Underlying(symbol)
        chain = await option_chain.get_option_chain(session, undl)
        LOGGER.info('Chain strikes: %s', chain.get_all_strikes())
    except Exception:
        LOGGER.error(f'Could not get options for {symbol}')


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
    user = environ.get('TW_USER', '')
    password = environ.get('TW_PASSWORD', '')
    if user == '':
        LOGGER.exception('Please provide username')
    if password == '':
        LOGGER.exception('Please provide password')
    tasty_client = tasty_session.create_new_session(user, password)

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
            task for task in asyncio.all_tasks() if not task.done()
        ]
        loop.run_until_complete(asyncio.gather(*pending_tasks))
        loop.close()


if __name__ == '__main__':
    main()
