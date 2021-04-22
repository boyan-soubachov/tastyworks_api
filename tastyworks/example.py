import asyncio
import calendar
import logging
import pandas as pd
from os import environ
from datetime import date, timedelta, time, datetime
from decimal import Decimal

from tastyworks.models import option_chain, underlying
from tastyworks.models.option import Option, OptionType
from tastyworks.models.greeks import Greeks
from tastyworks.models.quote import Quote
from tastyworks.models.order import (Order, OrderDetails, OrderPriceEffect, OrderType)
from tastyworks.models.session import TastyAPISession
from tastyworks.models.trading_account import TradingAccount
from tastyworks.models.underlying import UnderlyingType
from tastyworks.streamer import DataStreamer
from tastyworks.tastyworks_api import tasty_session

from tastyworks.dxfeed.mapped_item import MappedItem

LOGGER = logging.getLogger(__name__)


async def main_loop(session: TastyAPISession, streamer: DataStreamer):

    # OPEN ORDERS
    # # Get accounts
    # accounts = await TradingAccount.get_remote_accounts(session)
    # acct = accounts[1]
    # LOGGER.info('Accounts available: %s', accounts)

    # # Get open orders
    # orders = await Order.get_remote_orders(session, acct)
    # LOGGER.info('Number of active orders: %s', len(orders))
    #
    # # List all the open orders
    # for order in orders:
    #     print(order.details)

    # EQUITIES
    # Get quotes of equities
    symbols = ["SPY", "AAPL", "SPX"]
    streamer_list = {"Quote": symbols}
    await streamer.add_data_sub(streamer_list)
    # fetch the current data one time via streamer
    streamer_data = []
    async for item in streamer.listen():
        # LOGGER.info('Received item: %s' % item.data)
        streamer_data.extend(item.data)
        if streamer_data.__len__() == streamer_list['Quote'].__len__():
            await streamer.reset_data_subs()
            break  # Stops the async for item in streamer.listen() loop after receiving all the data

    # Store in a list
    print("--------------")
    quotes = []
    for data in streamer_data:
        qd = Quote(data)
        quotes.append(qd)
        print(f"Ticker: {qd.symbol}, Bid: {qd.bid_price}, Ask: {qd.ask_price}")
    print("--------------")

    # Storing in a dictionary nested with datetime string instead for maybe easier access
    print("--------------")
    quotes = dict.fromkeys(symbols, dict())
    for data in streamer_data:
        now_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        qd = Quote(data)
        quotes[qd.symbol][now_str] = qd
        print(f"Ticker: {qd.symbol}, "
              f"Date & Time: {list(quotes[qd.symbol].keys())[-1]}, "
              f"Bid: {quotes[qd.symbol][list(quotes[qd.symbol].keys())[-1]].bid_price}, "
              f"Ask: {quotes[qd.symbol][list(quotes[qd.symbol].keys())[-1]].ask_price}")
    print("--------------")

    # Example to keep collection quotes every 1 second until we have 10 data points
    # Kind of a hack of the streamer as it stops streaming during off hours it seems (but can get 1 set of values)
    # Storing in pandas dataframe for simplicity
    quotes = pd.DataFrame()
    while 1:
        await streamer.add_data_sub(streamer_list)
        # fetch the current data one time via streamer
        streamer_data = []
        async for item in streamer.listen():
            print("--------------")
            streamer_data.extend(item.data)
            for data in item.data:
                qd_df = pd.DataFrame.from_dict([data])
                qd_df['eventTime'] = datetime.now()
                quotes = quotes.append(qd_df)
                # dataframe entry can be converted to Quote() object
                qd = Quote(qd_df.iloc[0, :].to_dict())
                print(f'Received a total of {quotes.__len__()} quotes total so far.')
            print("--------------")
            streamer_data = []
            if quotes.__len__() >= 3:
                await streamer.reset_data_subs()
                print('pausing...')
                await asyncio.sleep(1)
                print('continuing...')
                break
        if quotes.__len__() >= 30:
            await streamer.reset_data_subs()
            break

    # # OPTIONS
    # Get an options chain for an underlying
    undl = underlying.Underlying('SPY')
    chain = await option_chain.get_option_chain(session, undl)
    exp = chain.get_all_expirations()
    # for expiration_date in exp:
    #     print(expiration_date)

    # Choose the next expiration as an example & fetch the entire options chain for that expiration (all strikes)
    next_exp = exp[0]
    chain_next_exp = await option_chain.get_option_chain(session, undl, next_exp)
    options = []
    # options_tickers = []
    for option in chain_next_exp.options:
        # LOGGER.info('> '
        #             f'{option.expiration_date}\t'
        #             f'{option.strike}\t'
        #             f'{option.option_type.value}\t'
        #             f'>>\tTicker {option.get_dxfeed_symbol()}')
        # options_tickers.append(option.get_dxfeed_symbol())
        option.get_dxfeed_symbol()
        options.append(option)

    # Get the data for all created symbols via the streamer by subscribing
    options_symbols = [options[x].symbol for x in range(options.__len__())]
    streamer_list = {
        # "Quote": [".SPY210419P410"]
        "Quote": options_symbols
    }
    await streamer.add_data_sub(streamer_list)

    # fetch the current data one time via streamer
    feed_data = []
    async for item in streamer.listen():
        # retrieve all the streamer data
        # !!! NOTE: streamer seems to retrieve a maximum of 100 items at a time
        #           so we need to check that we have all the data
        LOGGER.info(len(item.data))
        feed_data.extend(item.data)
        if feed_data.__len__() == streamer_list['Quote'].__len__():
            break  # Stops the async for item in streamer.listen() loop after receiving all the data

    # Process the streamer data to create the quotes list (not needed to get the greeks, just for example)
    quotes = []
    for data in feed_data:
        # LOGGER.info('Symbol: {}\tBid: {}\tAsk {}'.format(data['eventSymbol'], data['bidPrice'], data['askPrice']))
        # Create quote object
        qd = Quote(data)
        quotes.append(qd)

    # Get the Greeks for all the options
    # sub_greeks = {"Greeks": [".SPY210419P410"]}
    streamer_list = {"Greeks": options_symbols}
    await streamer.add_data_sub(streamer_list)

    greeks_data = []
    async for item in streamer.listen():
        # This is where you manipulate streamer data
        LOGGER.info(len(item.data))
        greeks_data.extend(item.data)
        if greeks_data.__len__() == streamer_list['Greeks'].__len__():
            break  # Stops the async for item in streamer.listen() loop after receiving all the data

    for data in greeks_data:
        gd = Greeks(data)
        idx_match = [x for x in range(options.__len__()) if options[x].symbol == gd.symbol][0]
        options[idx_match].greeks = gd
        LOGGER.info('> Symbol: {}\tPrice: {}\tDelta {}'.format(gd.symbol, gd.price, gd.delta))

    # # Execute an order
    # details = OrderDetails(
    #     type=OrderType.LIMIT,
    #     price=Decimal(400),
    #     price_effect=OrderPriceEffect.CREDIT)
    # new_order = Order(details)

    # opt = Option(
    #     ticker='AKS',
    #     quantity=1,
    #     expiration_date=get_third_friday(date.today()),
    #     strike=Decimal(3),
    #     option_type=OptionType.CALL,
    #     underlying_type=UnderlyingType.EQUITY
    # )
    # new_order.add_leg(opt)
    #
    # res = await acct.execute_order(new_order, session, dry_run=True)
    # LOGGER.info('Order executed successfully: %s', res)

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
    # finally:
    #     # find all futures/tasks still running and wait for them to finish
    #     pending_tasks = [
    #         task for task in asyncio.all_tasks() if not task.done()
    #     ]
    #     loop.run_until_complete(asyncio.gather(*pending_tasks))
    #     loop.close()


if __name__ == '__main__':
    main()
