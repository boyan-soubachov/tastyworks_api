import aiohttp


class Watchlist(object):
    def __init__(self, name=None, slug=None):
        self.name = name
        self.slug = slug
        self.securities = {}

    @classmethod
    def from_list(cls, data):
        inst = cls()
        for item in data:
            inst.securities[item['symbol']] = {
                'asset_type': item['asset_type']
            }
        return inst


class WatchlistGroup(object):
    def __init__(self):
        self.watchlists = {}

    async def load_watchlists(self, session):
        """
        Get's a users public watchlists.
        
        For user created watchlists use '/watchlists' instead.

        Args:
            session (TastyAPISession): The session to use.
        """

        request_url = '{}/public-watchlists'.format(
            session.API_url
        )

        async with aiohttp.request('GET', request_url) as resp:
            if resp.status != 200:
                raise Exception('Could not get public asset watchlists')
            data = await resp.json()

        data = data['public_watchlists']
        for entry in data:
            list_data = entry['entries']
            wlist = Watchlist.from_list(list_data)
            wlist.name = entry['name']
            wlist.slug = entry['slug']
            self.watchlists[wlist.slug] = wlist

        return self


def get_all_watchlists():
    return WatchlistGroup().load_watchlists()
