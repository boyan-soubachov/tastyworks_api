import asyncio
import logging

from tastyworks.models.order import (Order, OrderDetails, OrderPriceEffect,
                                     OrderType)
from tastyworks.models.session import TastyAPISession
from tastyworks.streamer import DataStreamer
from tastyworks.models.trading_account import TradingAccount
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

    accounts = await TradingAccount.get_remote_accounts(session)
    LOGGER.info('Trading accounts: %s', accounts)
    acct = accounts[0]

    orders = await Order.get_remote_orders(session, acct)
    LOGGER.info('Number of active orders: %s', len(orders))

    details = OrderDetails(
        underlying_symbol='AKS',
        type=OrderType.LIMIT,
        price=400,
        price_effect=OrderPriceEffect.CREDIT)
    new_order = Order(details)
    # res = await acct.execute_order(new_order, session, dry_run=True)
    # LOGGER.info('execute res: %s', res)

    await streamer.add_data_sub(sub_values)

    async for item in streamer.listen():
        LOGGER.info('Received item: %s' % item.data)


def main():
    tasty_client = tasty_session.create_new_session('your_username', 'your_password_here')

    streamer = DataStreamer(tasty_client)
    LOGGER.info('Streamer token: %s' % streamer.get_streamer_token())
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_loop(tasty_client, streamer))
    finally:
        # find all futures/tasks still running and wait for them to finish
        pending_tasks = [
            task for task in asyncio.Task.all_tasks() if not task.done()
        ]
        loop.run_until_complete(asyncio.gather(*pending_tasks))
        loop.close()


if __name__ == '__main__':
    main()
