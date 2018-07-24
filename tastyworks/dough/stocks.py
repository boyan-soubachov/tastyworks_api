import aiohttp

from tastyworks.dough import BASE_URL

"""
Performs a stock search through dough API

:param symbols: list of symbols (strings)
:returns: list of stock details including full name, implied volatility, liquidity etc.
:raises Exception: raises an exception when request is not 200 OK
"""
async def stock_search(symbols):    
    request_url = '{}/stocks/search/'.format(
        BASE_URL
    )

    payload = {
        "symbols" : symbols
    }    
    
    async with aiohttp.request('POST', request_url, json=payload) as resp:
        if resp.status != 200:
            raise Exception('Stock search failed')
        data = await resp.json()            
    
    return data["stocks"]    
