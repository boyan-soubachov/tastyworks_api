import asyncio
import logging

from tastyworks.streamer import DataStreamer
from tastyworks.tastyworks_api import tasty_session

LOGGER = logging.getLogger(__name__)


async def main_loop(streamer: DataStreamer):
    # sub_values = {
    #     "Greeks": [
    #         ".VIX180718C21",
    #         ".YUM180518C95"
    #     ]
    # }
    sub_values = {
        "Quote": ["/ES"]
    }
    await streamer.add_data_sub(sub_values)

    async for item in streamer.listen():
        LOGGER.info('Received item: %s' % item.data)


def main():
    tasty_client = tasty_session.TastyAPISession('your_tastyworks_username', 'your_tastyworks_password')
    LOGGER.info('Got client, token: %s' % tasty_client.get_streamer_token())

    streamer = DataStreamer(tasty_client)
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_loop(streamer))
    finally:
        # find all futures/tasks still running and wait for them to finish
        pending_tasks = [
            task for task in asyncio.Task.all_tasks() if not task.done()
        ]
        loop.run_until_complete(asyncio.gather(*pending_tasks))
        loop.close()


if __name__ == '__main__':
    main()
