from tastyworks.models.symbol_search import symbol_search
from tastyworks.tastyworks_api import tasty_session
import asyncio


class TestSymbolSearch(object):
    """Test Symbol Search

    Class to test symbol searching.

    Args:
        username (string): Tastyworks username
        password (string): Tastyworks password
    """

    def __init__(self, username: str, password: str, symbol: str = 'SPY'):
        self.session = tasty_session.create_new_session(
            username, password
        )
        self.data = asyncio.run(
            symbol_search(symbol, self.session)
        )
