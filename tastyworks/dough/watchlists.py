import aiohttp

from tastyworks.dough import BASE_URL


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

    async def load_watchlists(self):
        request_url = '{}/public_watchlists?include_synthetic=true'.format(
            BASE_URL
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


def get_all_watchlists():
    return WatchlistGroup.load_watchlists()
