import aiohttp
import inspect

from os import environ
from datetime import date
from urllib.parse import quote
from typing import Dict


async def is_error(resp, valid_list: list = None, error_list: list = None):
    # TODO: Improve to capture errors? Can use the 'ok' data of resp
    if valid_list is None:
        valid_list = [200, 201, 202]
    if error_list is None:
        error_list = []

    if resp.status not in valid_list or resp.status in error_list:
        print(
            f'###################################################\n'
            f'API returned an error for: {resp.request_info.url}\n'
            f'Called from: {inspect.stack()[2].function}\n'
            f'Response status: {resp.status}\n'
            f'Reason: {resp.reason}\n'
            f'###################################################'
        )
        return False
    else:
        return True


def make_api_url(key: str, **kwargs):
    """
    This will format all the API strings based on the **kwargs and pick the one to use based on the 'key'

    Args:
        key (str): The key to choose and return from the dictionary
        **kwargs: Input data needed depending on the type of request

    Returns:
        A formatted URL string made for the requested API call
    """
    symbol = kwargs.get('symbol')
    account = kwargs.get('account')
    start_date = kwargs.get('start_date')
    end_date = kwargs.get('end_date')
    tag = kwargs.get('tag')
    order_id = kwargs.get('order_id')
    entry_id = kwargs.get('entry_id')
    journal_page_offset = kwargs.get('journal_page_offset')
    watchlist_name = kwargs.get('watchlist_name')
    per_page = kwargs.get('per_page')
    page_number = kwargs.get('page_number')

    if not account:
        account = environ.get('TW_ACCOUNT', '')

    if type(symbol) is list:
        symbol = ','.join(symbol)

    if per_page:
        if key == 'TRANSACTIONS' and per_page > 2000:  # Transactions are limited to 2000
            print('Limited to 2000 items per page for transactions. Setting at 2000 per page.')
            per_page = 2000
        if key == 'ORDERS' and per_page > 200:  # Orders are limited to 200
            print('Limited to 200 items per page for orders. Setting at 200 per page.')
            per_page = 200

    root = 'https://api.tastyworks.com'

    crumbs = {
        'SESSION_START': '/sessions',
        'SESSION_VALIDATE': '/sessions/validate',
        'STREAMER_INFO': '/quote-streamer-tokens',

        'ACCOUNTS': '/customers/me/accounts',
        'BALANCES': f'/accounts/{account}/balances',
        'POSITIONS': f'/accounts/{account}/positions',
        'STATUS': f'/accounts/{account}/trading-status',

        'TRANSACTIONS': f'/accounts/{account}/transactions'
                        f'?start-date={quote(start_date if start_date else "", safe="")}'
                        f'&end-date={quote(end_date if end_date else "", safe="")}'
                        f'{"&underlying-symbol="+symbol if symbol else ""}'
                        f'{"&per-page="+str(per_page) if per_page else ""}'
                        f'{"&page-offset="+str(page_number-1) if page_number else ""}',

        'ORDERS': f'/accounts/{account}/orders?'
                  f'start-date={quote(start_date if start_date else "", safe="")}'
                  f'&end-date={quote(end_date if end_date else "", safe="")}'
                  f'{"&underlying-symbol="+symbol if symbol else "" }'
                  f'{"&per-page="+str(per_page) if per_page else ""}'
                  f'{"&page-offset="+str(page_number-1) if page_number else ""}',

        'ORDERS_LIVE': f'/accounts/{account}/orders/live',

        'ORDER_DRY_RUN': f'/accounts/{account}/orders{"/"+order_id if order_id else ""}/dry-run',
        'ORDER_EXECUTE': f'/accounts/{account}/orders{"/"+order_id if order_id else ""}',
        'FIFTY_POP': '/fifty-percent-pop',

        'SYMBOL_SEARCH': f'/symbols/search/{quote(symbol if symbol else "", safe="")}',  # TODO
        'MARKET_METRICS': f'/market-metrics?symbols={symbol}',  # TODO
        'OPTION_CHAINS': f'/option-chains/{symbol}/nested',  # TODO
        'FUTURE_OPTION_CHAINS': f'/futures-option-chains/{(symbol if symbol else "").strip("/")}/nested',  # TODO

        'WATCHLISTS': f'/watchlists{"/"+watchlist_name if watchlist_name else ""}',
        'WATCHLISTS_PUBLIC': '/public-watchlists',

        'INST_FUTURES': '/instruments/futures',
        'PRECISIONS': '/instruments/quantity-decimal-precisions',
        'JOURNAL': f'/journal-entries'
                   f'{"/"+entry_id if entry_id else ""}'  # Used for modifying or deleting an entry
                   f'{"?page-offset="+journal_page_offset if journal_page_offset else ""}'
                   f'{"&" if journal_page_offset else "?"}'
                   f'{"tag="+tag if tag else ""}'  # Used to search for an entry by tag
    }

    url = root + crumbs.get(key)
    return url


async def api_request(request_type: str, url: str, token: str = None, json_data: dict = None):
    """
    Get all the data from the TW API from a specific API URL and request type

    Args:
        request_type (str): Type of request ('GET', 'POST')
        url (str): url returned by APIUrl.METRICS.make_url()
        token (str): The TW API token from an open session
        json_data (dict): The JSON payload associated with the request
    Returns:
        The server response
    """
    print(f'##########\n'
          f'Running: {inspect.stack()[1].function}\n'
          f'##########')

    if token is not None:
        header = {'Authorization': token}
    else:
        header = {}

    async with aiohttp.request(request_type, url, headers=header, json=json_data) as resp:
        await is_error(resp)
        if resp:
            api_response = {
                'content': 'OK' if (resp.status == 202) else await resp.json(),  # 202 not returning any data
                'ok': resp.ok,
                'status': resp.status,
                'reason': resp.reason,
                'url': str(resp.url),
                'method': resp.method,
                'content_length': resp.content_length,
                'content_type': resp.content_type
            }
        else:
            api_response = {}

    return api_response


"""
#########################################
############### SESSION #################
#########################################
"""


async def session_start(username: str = None, password: str = None) -> Dict:
    """
    Start a TW API session.

    Args:
        username: TW account username
        password: TW account password

    Returns:
        The API server response containing the session token as well as user/account data
    """
    if username is None and password is None:
        body = {
            'login': environ.get('TW_USER', ""),
            'password': environ.get('TW_PASSWORD', "")
        }
    else:
        body = {
            'login': username,
            'password': password
        }

    url = make_api_url('SESSION_START')
    resp = await api_request('POST', url, json_data=body)
    return resp


async def session_validate(token: str) -> Dict:
    """
    Validate the status of a TW API session using the session token
    """
    url = make_api_url('SESSION_VALIDATE')
    resp = await api_request('POST', url, token)
    return resp


async def get_streamer_info(token: str) -> Dict:
    """
    Get the streamer information including URL and token (take in the different TW session token)
    """
    url = make_api_url('STREAMER_INFO')
    resp = await api_request('GET', url, token)
    return resp


"""
#########################################
############### ACCOUNT #################
#########################################
"""


async def get_accounts(token: str) -> Dict:
    """
    Requests the account numbers using the session token
    """
    url = make_api_url('ACCOUNTS')
    resp = await api_request('GET', url, token)
    return resp


async def get_balances(token: str, account_number: str) -> Dict:
    """
    Requests the balances for a specific account number using the session token
    """
    url = make_api_url('BALANCES', account=account_number)
    resp = await api_request('GET', url, token)
    return resp


async def get_positions(token: str, account_number: str) -> Dict:
    """
    Retrieves all the positions for a specific account number using the session token
    """
    url = make_api_url('POSITIONS', account=account_number)
    resp = await api_request('GET', url, token)
    return resp


async def get_status(token: str, account_number: str) -> Dict:
    """
    Retrieves the status of an account
    """
    url = make_api_url('STATUS', account=account_number)
    resp = await api_request('GET', url, token)
    return resp


"""
#########################################
######## TRANSACTIONS & ORDERS ##########
#########################################
"""


async def get_transactions(token: str, account_number: str = '', symbol: str = '',
                           start_date: date = None, end_date: date = None,
                           per_page: int = None, page_number: int = None) -> Dict:
    """
    Retrieves all the transactions for the TW API for the TW API for a specific account
    (limited to a max of 2000 per page)

    Args:
        token (str): A valid session token
        account_number (str): Account number to check
        symbol (str): A equity or future symbol
        start_date (date): a date object representing the day for the start of the date rance
        end_date (date): a date object representing the day for the end of the date range
        per_page (int): how many items to retrieve per page of data (max 2000 for orders)
        page_number (int): the page number to retrieve (non existing page number will return an empty list)

    Returns:
        The API server response containing including a list of transactions and the pagination information
        (can be used to loop through all the pages)
    """
    if start_date:
        start_date = start_date.strftime('%Y-%m-%dT08:00:00.000Z')
    if end_date:
        end_date = end_date.strftime('%Y-%m-%dT07:00:00.000Z')

    url = make_api_url('TRANSACTIONS',
                       account=account_number,
                       symbol=symbol,
                       start_date=start_date,
                       end_date=end_date,
                       per_page=per_page,
                       page_number=page_number)
    resp = await api_request('GET', url, token)
    return resp


async def get_orders(token: str, account_number: str = '', symbol: str = '',
                     start_date: date = None, end_date: date = None,
                     per_page: int = None, page_number: int = None) -> Dict:
    """
    Retrieves all the transactions for the TW API for the TW API for a specific account
    (limited to a max of 200 per page)

    Args:
        token (str): A valid session token
        account_number (str): Account number to check
        symbol (str): A equity or future symbol
        start_date (date): a date object representing the day for the start of the date rance
        end_date (date): a date object representing the day for the end of the date range
        per_page (int): how many item to retrieve per page of data (max 200 for orders)
        page_number (int): the page number to retrieve (non existing page number will return an empty list)

    Returns:
        The API server response containing a list of orders and the pagination information
        (can be used to loop through all the pages)
    """
    if start_date:
        start_date = start_date.strftime('%Y-%m-%dT08:00:00.000Z')
    if end_date:
        end_date = end_date.strftime('%Y-%m-%dT07:00:00.000Z')

    url = make_api_url('ORDERS',
                       account=account_number,
                       symbol=symbol,
                       start_date=start_date,
                       end_date=end_date,
                       per_page=per_page,
                       page_number=page_number)
    resp = await api_request('GET', url, token)
    return resp


async def get_orders_live(token: str, account_number: str) -> Dict:
    """
    Retrieves all the orders for today (working, closed, executed, etc.)
    """
    url = make_api_url('ORDERS_LIVE', account=account_number)
    resp = await api_request('GET', url, token)
    return resp


async def route_order(token: str, account_number: str, order_json: dict,
                      is_dry_run: bool = True, order_id: str = None) -> Dict:
    """
    Place a dry-run (preview), route a live order or allow to modify an order by passing the additional "order_id".

    Args:
        token (str): A valid session token
        account_number (str): Account number to check
        order_json (dict): The order payload containing the expected order information
        is_dry_run (bool): True for a order review (dry-run) and False to route the order
        order_id (str): An order 'id' read from an open orders list received via get_orders() or get_orders_live().
                        It is an optional input parameter to place a new order.
                        This is required to modify an order for dry run or order routing.

    Returns:
        The response from the server after dry-run or routing the order including all the order information.
    """

    if is_dry_run:
        url = make_api_url('ORDER_DRY_RUN', account=account_number, order_id=order_id)
    else:
        url = make_api_url('ORDER_EXECUTE', account=account_number, order_id=order_id)

    if order_id:
        resp = await api_request('PATCH', url, token, json_data=order_json)
    else:
        resp = await api_request('POST', url, token, json_data=order_json)
    return resp


async def cancel_order(token: str, account_number: str, order_id: str = None) -> Dict:
    """
    Cancels an open order defined by "order_id"
    Args:
        token (str): A valid session token
        account_number (str): Account number to use
        order_id (str): An order 'id' read from an open orders list received via get_orders() or get_orders_live().
                        It is an optional input parameter to place a new order.
                        This is required to modify an order for dry run or order routing.

    Returns:
        The response from the server after canceling the order
    """
    # TODO: What is the request and response for the "CANCEL ALL ORDERS" button in the TW platform?
    #       Could not test on live account

    url = make_api_url('ORDER_EXECUTE', account=account_number, order_id=order_id)
    resp = await api_request('DELETE', url, token)
    return resp


async def fifty_percent_pop(token: str, pop_json: dict) -> Dict:
    """
    Returns the response of the API server including statistical analysis data of a simulated order.
    JSON data include parameters that needs to be retrieved via market metrics and other API calls.
    """
    url = make_api_url('FIFTY_POP')
    resp = await api_request('POST', url, token, json_data=pop_json)
    return resp


"""
################################
######## TRADING DATA ##########
################################
"""


async def symbol_search(token: str, symbol: str) -> Dict:
    """
    Performs a symbol search using Tastyworks API.

    This returns a list of symbols that are similar to the symbol passed in the parameters. This does not provide
    any details except the related symbols and their descriptions.

    Args:
        token (str): A valid session token
        symbol (string): A base symbol (or first characters of a symbol) to search for symbols starting with the string

    Returns:
        The response from the API server including a list of dictionaries containing the symbols that start with the
        passed symbol string and a descriptions for each of the found symbols, i.e.
            [{'symbol': 'K', 'description': 'Kellogg Company Common Stock'},
            {'symbol': 'KB', 'description': 'KB Financial Group Inc'}]
    """
    url = make_api_url('SYMBOL_SEARCH', symbol=symbol)
    resp = await api_request('GET', url, token)
    return resp


async def get_market_metrics(token: str, symbol_list: list) -> Dict:
    """
    Get the market metrics for a symbol or a list of symbols

    Args:
        token (str): A valid session token
        symbol_list (list): A base symbol to search for similar symbols

    Returns:
       The response from the API server including a list of dictionaries containing the symbols that start with
       the passed symbol string and all the market data for each of the found symbols, i.e.
            [{'symbol': 'K', 'implied-volatility-index': '0.179364648'},
            {'symbol': 'KB', 'implied-volatility-index': '0.183716246'}]
    """
    url = make_api_url('MARKET_METRICS', symbol=symbol_list)
    resp = await api_request('GET', url, token)
    return resp


async def get_options_chain(token: str, symbol: str) -> Dict:
    """
    Get an option chain for an underlying symbol (Equity or Future).

    Args:
        token (str): A valid session token
        symbol (string): A base symbol (or first characters of a symbol) to search for symbols starting with the string

    Returns:
        The response from the API server including a list of dictionaries containing the symbols that start with
        the passed symbol string and all the option chains for each of the found symbols
    """

    if symbol[0] == '/':
        url = make_api_url('FUTURE_OPTION_CHAINS', symbol=symbol)
    else:
        url = make_api_url('OPTION_CHAINS', symbol=symbol)

    resp = await api_request('GET', url, token)
    return resp


"""
#########################################
############# WATCHLISTS ################
#########################################
"""


async def get_watchlists(token: str) -> Dict:
    """
    Retrieves the account personal watchlists
    """
    url = make_api_url('WATCHLISTS')
    resp = await api_request('GET', url, token)
    return resp


async def create_watchlist(token: str, watchlist_json: dict) -> Dict:
    """
    Creating a watchlist requires watchlist name and the JSON payload including the symbols to include
    TODO: Will fail if watchlist name already exists, we may want to check or catch the error
    """
    url = make_api_url('WATCHLISTS')
    resp = await api_request('POST', url, token, json_data=watchlist_json)
    return resp


async def update_watchlist(token: str, watchlist_name: str, watchlist_json: dict) -> Dict:
    """
    Adding and removing a symbol from a list requires the watchlist name and a new JSON payload.
    """
    url = make_api_url('WATCHLISTS', watchlist_name=watchlist_name)
    resp = await api_request('PUT', url, token, json_data=watchlist_json)
    return resp


async def delete_watchlist(token: str, watchlist_name: str) -> Dict:
    """
    Deleting a watchlist using its name and a DELETE method
    """
    url = make_api_url('WATCHLISTS', watchlist_name=watchlist_name)
    resp = await api_request('DELETE', url, token)
    return resp


async def get_watchlists_public(token: str) -> Dict:
    """
    Retrieves the public TW watchlists

    """
    url = make_api_url('WATCHLISTS_PUBLIC')
    resp = await api_request('GET', url, token)
    return resp


"""
#########################################
############### JOURNAL #################
#########################################
"""


async def get_journal_entries(token: str, tag: str = None, journal_page_offset: str = None) -> Dict:
    """
    Retrieves the account journal entries for the first page (10 entries)
    Note: The tags don't seem to work when entering any Symbol, only tags seems to work (and must be exact tags!)
    Note: Also shows some pagination field in the response, not sure what they do, not returned here for simplicity
    """
    url = make_api_url('JOURNAL', tag=tag, journal_page_offset=journal_page_offset)
    resp = await api_request('GET', url, token)
    return resp


async def add_journal_entry(token: str, entry_json: dict) -> Dict:
    """
    Add a new journal entry. Entry can be linked to a specific order or not
    Passing the entry_id will allow to update/override the entry (entire JSON content needs to be sent)
    """
    url = make_api_url('JOURNAL')
    resp = await api_request('POST', url, token, json_data=entry_json)
    return resp


async def update_journal_entry(token: str, entry_json: dict, entry_id: str = None) -> Dict:
    """
    Passing the entry_id will allow to update/override the entry via a PUT request
    Entire JSON content for the new entry needs to be sent as if creating a new entry
    Will only return that the change has been accepted (no response from the API)
    """
    url = make_api_url('JOURNAL', entry_id=entry_id)
    resp = await api_request('PUT', url, token, json_data=entry_json)
    return resp


async def delete_journal_entry(token: str, entry_id: str = None) -> Dict:
    """
    Delete a journal entry by its ID
    Will only return that the change has been accepted (no response from the API)
    """
    url = make_api_url('JOURNAL', entry_id=entry_id)
    resp = await api_request('DELETE', url, token)
    return resp


"""
#########################################
################ MISC ###################
#########################################
"""


async def get_instruments_futures(token: str) -> Dict:
    """
    Retrieves a list of all current future products
    """
    url = make_api_url('INST_FUTURES')
    resp = await api_request('GET', url, token)
    return resp


async def get_instruments_precisions(token: str) -> Dict:
    """
    Retrieves a list of the various decimal precision for TW available instruments including crypto pairs
    """
    url = make_api_url('PRECISIONS')
    resp = await api_request('GET', url, token)
    return resp

