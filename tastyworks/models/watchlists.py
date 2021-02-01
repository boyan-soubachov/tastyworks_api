import aiohttp
from tastyworks.models.session import TastyAPISession


class Watchlist(object):
    def __init__(self, name=None):
        self.name = name
        self.group_name = None
        self.securities = {}

    @classmethod
    def from_list(cls, data: list):
        """From List

        Generator for making a watchlist.

        Notes:
            There is an instability issue with Tastyworks API.  Hence
            the need to catch an exception.  Special symbols don't have
            instrument-type's at all.

        Args:
            data (list):   List of dict objects containing symbol &
                           [instrument-type | instrument_type] keys.

        Returns:
            Watchlist:  A watchlist object
        """
        inst = cls()
        for item in data:
            try:
                inst.securities[item['symbol']] = {
                    'instrument-type': item['instrument-type']
                }
            except KeyError:
                try:
                    inst.securities[item['symbol']] = {
                        'instrument_type': item['instrument_type']
                    }
                except KeyError:
                    inst.securities[item['symbol']] = {
                        'instrument-type': None
                    }
        return inst


class WatchlistGroup(object):
    """Watchlist Group

    Generator for making document of watchlist objects.

    Notes:
        Not all watchlists return group-name key's.  Hence the need to catch
        an exception.

    Args:
        session (TastyAPISession): Tastyworks API Session object
        public (boolean): True if retrieving public-watchlists, false if
                          retrieving custom-watchlists

    Returns:
        WatchlistGroup: A group of watchlists

    """
    def __init__(self):
        self.watchlists = {}

    async def load_watchlists(
        self, session: TastyAPISession, public: bool = True
    ):
        url = f'{session.API_url}/public-watchlists' if public else f'{session.API_url}/watchlists'  # NOQA: E501

        async with aiohttp.request(
            'GET', url, headers=session.get_request_headers()
        ) as resp:
            if resp.status != 200:
                raise Exception('Could not get public asset watchlists')
            data = await resp.json()

        data = data['data']['items']
        for entry in data:
            list_data = entry['watchlist-entries']
            wlist = Watchlist.from_list(list_data)
            wlist.name = entry['name']
            try:
                wlist.group_name = entry['group-name']
            except KeyError:
                pass
            self.watchlists[wlist.name] = wlist

        return self


def get_all_watchlists(session: TastyAPISession, public: bool = True):
    return WatchlistGroup().load_watchlists(session, public=public)
