import asyncio
import logging

from tastyworks.streamer import DataStreamer
from tastyworks.tastyworks_api import tasty_session
from tastyworks.models.session import TastyAPISession

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

    # get all active orders
    orders = await session.get_active_orders()
    LOGGER.info('Number of active orders: %s', len(orders))

    # set up some streamers
    await streamer.add_data_sub(sub_values)

    async for item in streamer.listen():
        LOGGER.info('Received item: %s' % item.data)


def main():
    tasty_client = tasty_session.create_new_session('your_tastyworks_username', 'your_tastyworks_password')

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
