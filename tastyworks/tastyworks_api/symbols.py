import aiohttp

BASE_URL = 'https://trade.tastyworks.com'


async def search_symbol(query):
    request_url = '{}/symbol_search/search/{}'.format(BASE_URL, query)
    async with aiohttp.request('GET', request_url) as resp:
        if resp.status != 200:
            raise Exception('Could not search for symbol {}', query)
        resp = await resp.json()
        return [entry[0] for entry in resp]
