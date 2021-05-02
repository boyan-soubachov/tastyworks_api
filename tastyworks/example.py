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
from tastyworks.models.greeks import Greeks

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
        ticker='SPY',
        quantity=1,
        expiry=get_third_friday(date.today()),
        strike=Decimal(500),
        option_type=OptionType.CALL,
        underlying_type=UnderlyingType.EQUITY
    )
    new_order.add_leg(opt)

    res = await acct.execute_order(new_order, session, dry_run=True)
    LOGGER.info('Order executed successfully: %s', res)

    # Get an options chain
    undl = underlying.Underlying('SPY')
    chain = await option_chain.get_option_chain(session, undl)
    LOGGER.info('Chain strikes: %s', chain.get_all_strikes())

    # Get all expirations for the options for the above equity symbol
    exp = chain.get_all_expirations()

    # Choose the next expiration as an example & fetch the entire options chain for that expiration (all strikes)
    next_exp = exp[0]
    chain_next_exp = await option_chain.get_option_chain(session, undl, next_exp)
    options = []
    for option in chain_next_exp.options:
        options.append(option)

    # Get the greeks data for all option symbols via the streamer by subscribing
    options_symbols = [options[x].symbol_dxf for x in range(len(options))]
    streamer_list = {"Greeks": options_symbols}
    await streamer.add_data_sub(streamer_list)
    greeks_data = []

    async for item in streamer.listen():
        # This is where you manipulate incoming streamer data
        greeks_data.extend(item.data)
        if len(greeks_data) >= len(streamer_list['Greeks']):
            break  # Stops the async for item in streamer.listen() loop after receiving all the data

    for data in greeks_data:
        gd = Greeks().from_streamer_dict(data)
        # gd = Greeks(kwargs=data)
        idx_match = [options[x].symbol_dxf for x in range(len(options))].index(gd.symbol)
        options[idx_match].greeks = gd
        LOGGER.info('> Symbol: {}\tPrice: {}\tDelta {}'.format(gd.symbol, gd.price, gd.delta))
        # print('> Option with Greeks:\n', options[idx_match])

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
    tasty_client = tasty_session.create_new_session(environ.get('TW_USER', ""), environ.get('TW_PASSWORD', ""))

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
