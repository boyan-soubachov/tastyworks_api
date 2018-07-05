import aiohttp

from tastyworks.dough import BASE_URL


async def stock_search(symbols):
    """
    Performs a stock search through the dough API.

    Args:
        symbols (list): The list of string symbols to search for.

    Returns:
        list (dict): A list of stock details including full name, implied volatility, liquidity etc.

    Raises:
        Exception: raises a general exception when the request does not succeed.
    """

    request_url = '{}/stocks/search/'.format(
        BASE_URL
    )

    payload = {
        'symbols': symbols
    }

    async with aiohttp.request('POST', request_url, json=payload) as resp:
        if resp.status != 200:
            raise Exception(
                'Searching for stocks {} failed'.format(', '.join(payload['symbols']))
            )
        data = await resp.json()

    return data["stocks"]
