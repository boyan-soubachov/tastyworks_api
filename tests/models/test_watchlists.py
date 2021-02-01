from tastyworks.models import watchlists
from tastyworks.tastyworks_api import tasty_session
import asyncio


class TestWatchlists(object):
    """Test Watchlists

    Class to test watchlist groups and watchlists.

    Args:
        username (string): Tastyworks username
        password (string): Tastyworks password
    """

    def __init__(self, username: str, password: str, public: bool = True):
        self.session = tasty_session.create_new_session(
            username, password
        )
        self.wlg = asyncio.run(
            watchlists.get_all_watchlists(self.session, public=public)
        )
