import asyncio
import logging
from os import environ
from datetime import date, timedelta

import tastyworks.tastyworks_api.tw_api as api

LOGGER = logging.getLogger(__name__)


async def main():
    """
    This shows example of the low level API calls.
    These calls do not replace the classes but instead should be called from the classes to interact with the API
    This allows for one single module for the API instead of having links spread out across modules and classes
    To import in classes, use:
        import tastyworks.tastyworks_api.tw_api as api
    """

    """
    #################
    # SESSION STUFF #
    #################
    """
    # Opens a new session and returns session token and user data
    resp = await api.session_start(environ.get('TW_USER', ""), environ.get('TW_PASSWORD', ""))
    session_token = resp.get('content').get('data').get('session-token')
    print(resp)

    # Get data back from a session validation
    resp = await api.session_validate(session_token)
    print(resp)

    """
    #################
    # ACCOUNT STUFF #
    #################
    """
    # Get raw accounts data from API
    resp = await api.get_accounts(session_token)
    print(resp)

    # Get a specific account balances from account number
    resp = await api.get_balances(session_token, environ.get('TW_ACCOUNT', ""))
    print(resp)

    # Get the status of an account
    resp = await api.get_status(session_token, environ.get('TW_ACCOUNT', ""))
    print(resp)

    # Get the data streamer token (for live data feed streamer)
    resp = await api.get_streamer_info(session_token)
    print(resp)

    """
    ##################
    # OPEN POSITIONS #
    ##################
    """
    # Get all the open positions for an account
    resp = await api.get_positions(session_token, environ.get('TW_ACCOUNT', ""))
    print(resp)

    """
    ##############
    # WATCHLISTS #
    ##############
    """
    # Get all the watchlists from the account
    resp = await api.get_watchlists(session_token)
    print(resp)

    # Create a new watchlist
    watchlist_json = {
        "name": "WL1234",
        "watchlist-entries": [
            {
                "symbol": "SPY",
                "instrument-type": "Equity"
            },
            {
                "symbol": "PEP",
                "instrument-type": "Equity"}
        ]
    }
    resp = await api.create_watchlist(session_token, watchlist_json)
    watchlist_name = resp.get('content').get('data').get('name')
    print(resp)

    # Updating a watchlist (adding or removing items) is done by creating a new JSON payload to an existing list
    watchlist_json = {
        "name": watchlist_name,
        "watchlist-entries": [
            {
                "symbol": "KO",
                "instrument-type": "Equity"
            },
            {
                "symbol": "AAPL",
                "instrument-type": "Equity"
            }
        ]
    }
    resp = await api.update_watchlist(session_token, watchlist_name, watchlist_json)
    print(resp)

    # Deleting a watchlist
    resp = await api.delete_watchlist(session_token, watchlist_name)
    print(resp)

    # Get all the public watchlists from TW platform
    resp = await api.get_watchlists_public(session_token)
    print(resp)

    """
    ###########
    # JOURNAL #
    ###########
    """
    # Add a journal entry with no order linked
    new_entry = {
        "title": "I rock!",
        "content": "I traded like a beast today",
        "tags": [
            "123"
        ],
    }
    resp = await api.add_journal_entry(session_token, entry_json=new_entry)
    entry_id = resp.get('content').get('data').get('id')
    print(resp)

    # Update a journal entry with no order linked
    corrected_entry = {
        "title": "Corrected: I rock!",
        "content": "Correction: I traded like a rock star today",
        "tags": [
            "123",
            "456"
        ],
    }
    resp = await api.update_journal_entry(session_token, entry_json=corrected_entry, entry_id=entry_id)
    print(resp)

    # Delete a journal entry by ID (deleting the one created above)
    resp = await api.delete_journal_entry(session_token, entry_id=entry_id)
    print(resp)

    # Add a journal entry with an order linked - A completely fake order still seems to work and show in the platform
    new_entry = {
        "title": "I rock too 2!",
        "content": "I traded like a rock star today",
        "end-state": "Winner",
        "tags": [
            "123"
        ],
        "order": {
            "source": "WBT",
            "order-type": "Limit",
            "legs": [
                {
                    "instrument-type": "Equity Option",
                    "symbol": "SPY   210618C00140000",
                    "action": "Sell to Open",
                    "quantity": "1"
                },
                {
                    "instrument-type": "Equity Option",
                    "symbol": "SPY   210507C00137000",
                    "action": "Buy to Close",
                    "quantity": "1"
                }
            ],
            "id": "123456",
            "received-at": "2021-04-26T12:51:40.017-07:00",
            "filled-at": "2021-04-27T21:36:29.964-07:00",
            "underlying-symbol": "SPY"
        }
    }
    resp = await api.add_journal_entry(session_token, entry_json=new_entry)
    entry = resp.get('content').get('data')
    entry_id = entry.get('id')
    print(resp)

    # Get the first page of journal entries (will fetch first 10 on the first page)
    resp = await api.get_journal_entries(session_token)
    entries = resp.get('content').get('data').get('items')
    pagination = resp.get('content').get('pagination')
    print(entries)

    # Get all the pages of journal entries using pagination, passing the pagination data from the first page
    # Other pagination information do not seems to be used or populated at all
    page = 2
    while pagination.get('next-link'):
        print(f'page #{page} [next-link={pagination.get("next-link")}]')
        resp = await api.get_journal_entries(session_token, journal_page_offset=pagination.get('next-link'))
        entries = resp.get('content').get('data').get('items')
        pagination = resp.get('content').get('pagination')
        page += 1
        print(entries)

    # Get the account journal entries that match the 'exact' tag (must be exact as seen in the entry)
    # 04/27/2021: Tag doesn't always work...... and symbol search does not work at all.......
    tag = '123'
    resp = await api.get_journal_entries(session_token, tag=tag)
    entries = resp.get('content').get('data').get('items')
    pagination = resp.get('content').get('pagination')
    print(entries)

    # Tag can also be combined with pagination
    page = 2
    while pagination.get('next-link'):
        print(f'page #{page} [next-link={pagination.get("next-link")}]')
        resp = await api.get_journal_entries(session_token, tag=tag, journal_page_offset=pagination.get('next-link'))
        entries = resp.get('content').get('data').get('items')
        pagination = resp.get('content').get('pagination')
        print(entries)
        page += 1

    # Delete a journal entry again to clean up the example (deleting the one created above)
    resp = await api.delete_journal_entry(session_token, entry_id=entry_id)
    print(resp)

    """
    ##################
    # READING ORDERS #
    ##################
    """
    # Get all the orders starting with open orders at the top of the list
    # All routed orders (canceled, executed, pending, etc.).

    # Can pass nothing to get all last orders (default last 10 orders)
    resp = await api.get_orders(session_token, environ.get('TW_ACCOUNT', ""))
    print(resp)

    # Can pass a symbol to get all last orders for that symbol (default last 10 orders)
    resp = await api.get_orders(session_token, environ.get('TW_ACCOUNT', ""), symbol='SPY')
    print(resp)

    # Can pass pagination to get less or more orders (orders max per page is 200) - Getting last 50 here
    resp = await api.get_orders(session_token, environ.get('TW_ACCOUNT', ""), per_page=50)
    print(resp)

    # Can pass pagination to get less or more orders (orders max per page is 200) - Getting 200 per page with page #
    resp = await api.get_orders(session_token, environ.get('TW_ACCOUNT', ""),
                                per_page=200, page_number=1)
    print(resp)

    symbol = 'SPY'
    start_date = date.today() - timedelta(days=90)
    end_date = date.today()

    # Can pass symbol, start date and end date as date objects for orders
    resp = await api.get_orders(session_token, environ.get('TW_ACCOUNT', ""), symbol=symbol,
                                start_date=start_date, end_date=end_date)
    print(resp)

    # Can pass symbol only to return last orders (up to 200 orders)
    resp = await api.get_orders(session_token, environ.get('TW_ACCOUNT', ""), symbol=symbol)
    print(resp)

    # Getting all of 'live' orders (all of today's open, executed, cancelled, rejected, etc.) - No pagination here
    resp = await api.get_orders_live(session_token, environ.get('TW_ACCOUNT', ""))
    print(resp)

    """
    ##################
    # ROUTING ORDERS #
    ##################
    """
    # Does not yet work with Future Options
    # TODO: Future options order leg symbol needs to also be figured out i.e "./MESM1EX2K1 210514P3900"
    # Returns the order acknowledgement, warnings, buying power and fees sheet
    # This requires building the order and the legs
    # Hardcoding JSON message for the example here. It should be build dynamically using Order object/methods.
    # Purposefully not using the existing classes for this example to keep this low level API example.

    # Example of a stock buy order: GTD, limit order, buy to open, dry-run (i.e. preview)
    order_json = {
        "source": "WBT",
        "order-type": "Limit",
        "time-in-force": "GTD",
        "gtc-date": "2026-05-31",
        "price": "999.00",
        "price-effect": "Debit",
        "legs": [
            {
                "instrument-type": "Equity",
                "symbol": "AAPL",
                "action": "Buy to Open",
                "quantity": "1"
            }
        ]
    }
    resp = await api.route_order(session_token, environ.get('TW_ACCOUNT', ""), order_json, is_dry_run=True)
    print(resp.get('content').get('data').get('order'))
    print(resp.get('content').get('data').get('warnings'))
    print(resp.get('content').get('data').get('buying-power-effect'))
    print(resp.get('content').get('data').get('fee-calculation'))

    # Example of an Equity Option order:
    # GTC, limit order, next Friday expiration, put, sell to open, dry-run (i.e. preview)
    symbol = 'SPY'
    option_type = 'P'
    exp_date = date.today()
    strike = 400
    while exp_date.weekday() != 4:
        exp_date += timedelta(1)
    # OCC Option Symbol
    symbol = symbol.ljust(6) + exp_date.strftime("%y%m%d") + option_type + str(strike * 1000).zfill(8)

    order_json = {
        'source': 'WBT',
        'order-type': 'Limit',
        'time-in-force': 'GTC',
        'price': '999.00',
        'price-effect': 'Credit',
        'legs': [
            {
                'instrument-type': 'Equity Option',
                'symbol': symbol,
                'action': 'Sell to Open',
                'quantity': '1'
            }
        ]
    }
    resp = await api.route_order(session_token, environ.get('TW_ACCOUNT', ""), order_json, is_dry_run=True)
    print(resp)

    # Example of the same as above but as a !!! real order !!!
    # THIS WILL ROUTE A REAL ORDER, HOWEVER, AT $999.00 PRICE (CREDIT) IT WILL NOT FILL
    # May be rejected depending on your account
    resp = await api.route_order(session_token, environ.get('TW_ACCOUNT', ""), order_json, is_dry_run=False)
    print(resp)
    order_id = ''
    if resp.get('ok'):
        order_id = str(resp.get('content').get('data').get('order').get('id'))

    # Getting the live orders to check if the order was accepted and is working (not rejected)
    # This would probably already be in the Order objet when using classes as part of order confirmation methods
    # Order validation should be implemented carefully with combination of order and transactions checks
    await asyncio.sleep(2)
    resp = await api.get_orders_live(session_token, environ.get('TW_ACCOUNT', ""))
    orders = resp.get('content').get('data').get('items')
    exist = False  # Setting false by default
    is_editable = False  # Setting false by default
    status = ''  # Setting as empty by default so that only confirmed Live order are acted upon
    for order in orders:
        if str(order.get('id')) == order_id:
            exist = True
            status = order.get('status')
            is_editable = order.get('editable')

    # Editing an order is also done via 'route_order' but it includes an order ID and a shortened JSON dictionary
    # Running this if the above order is Live and can be edited (seems to happen sometimes with the high price)
    if exist and status == 'Live' and is_editable:
        edited_order_json = {
            'source': 'WBT',
            'order-type': 'Limit',
            'time-in-force': 'GTC',
            'price': '777.00',
            'price-effect': 'Credit'
        }
        resp = await api.route_order(session_token, environ.get('TW_ACCOUNT', ""),
                                     order_json=edited_order_json, is_dry_run=False, order_id=order_id)
        order_id = str(resp.get('content').get('data').get('id'))
        print(resp)  # Note: The response is different when modifying, only getting the order

    # Need to get the new list of live orders again to check if the modified order was accepted and is live
    await asyncio.sleep(2)
    resp = await api.get_orders_live(session_token, environ.get('TW_ACCOUNT', ""))
    orders = resp.get('content').get('data').get('items')
    exist = False
    is_cancellable = False
    status = ''
    for order in orders:
        if str(order.get('id')) == order_id:
            exist = True
            status = order.get('status')
            is_cancellable = order.get('cancellable')

    # Cancelling an order using its 'order-id' if it has been accepted and is working
    if exist and status == 'Live' and is_cancellable:
        resp = await api.cancel_order(session_token, environ.get('TW_ACCOUNT', ""), order_id=order_id)
        print(resp)

    # Statistical analysis of an order, probability of 50% profit (not sure why json says 55%)
    # Here is a sale of a SPY 400 PUT with SPY at $418 and vol at 17.3% for a $1.1 credit to open
    pop_json = {
        "target-fraction-of-cost": 0.55,
        "initial-cost": 1.1,
        "initial-cost-effect": "Credit",
        "volatility": 0.173848732,
        "interest-rate": 0.02,
        "current-stock-price": 418.46500000000003,
        "histogram-ideal-range-count": 30,
        "legs": [
            {
                "quantity": "1",
                "strike-price": 400,
                "action": "selltoopen",
                "call-or-put": "P",
                "days-to-expiration": 15,
                "asset-type": "Equity Option",
                "contract-implied-volatility": 0.1836899,
                "expiration-implied-volatility": 0.154691963
            }
        ]
    }
    resp = await api.fifty_percent_pop(session_token, pop_json=pop_json)
    print(resp)

    """
    ################
    # TRANSACTIONS #
    ################
    """
    # Can pass no sorting parameters to get all transactions (default 250 transactions)
    resp = await api.get_transactions(session_token, environ.get('TW_ACCOUNT', ""))
    print(resp)

    # Can pass pagination to get less or more transactions (transactions max per page is 2000)
    resp = await api.get_transactions(session_token, environ.get('TW_ACCOUNT', ""), per_page=2000)
    print(resp)

    # Can pass symbol, start date and end date as date objects (looking for 'SPY transactions for the last 90 days here)
    symbol = 'SPY'
    start_date = date.today() - timedelta(days=90)
    end_date = date.today()
    resp = await api.get_transactions(session_token, environ.get('TW_ACCOUNT', ""), symbol=symbol,
                                      start_date=start_date, end_date=end_date)
    print(resp)

    # Works for future but must be the complete symbol with expiration cycle code. Will not work with just '/MES'.
    # Expirations symbols can be retrieved via api.get_options_chain(session_token, '/MES') in the 'futures' response
    resp = await api.get_options_chain(session_token, '/MES')
    symbol = resp.get('content').get('data').get('futures')[0].get('symbol')
    resp = await api.get_transactions(session_token, environ.get('TW_ACCOUNT', ""), symbol=symbol)
    print(resp)

    # Can also pass dates (default 250 transactions between these dates)
    resp = await api.get_transactions(session_token, environ.get('TW_ACCOUNT', ""),
                                      start_date=start_date, end_date=end_date)
    print(resp)

    """
    ################
    # TRADING DATA #
    ################
    """
    # Searching symbol works only for one string (finding all symbols starting with this string)
    resp = await api.symbol_search(session_token, 'SPY')
    print(resp)

    # Searching also works for futures with '/'
    resp = await api.symbol_search(session_token, '/MES')
    print(resp)

    # Searching also works for symbols with special characters '/'
    resp = await api.symbol_search(session_token, 'BRK/A')
    print(resp)

    # Searching also works for symbols for small exchange product with ':'
    resp = await api.symbol_search(session_token, 'FX:SME')
    print(resp)

    # Getting market metrics for one symbol in a list (will also work with a string, even though expecting a list)
    resp = await api.get_market_metrics(session_token, ['PEP'])
    print(resp)

    # Getting market metrics for multiple symbols in a list
    resp = await api.get_market_metrics(session_token, ['SPY', 'VIX', 'BRK/B', '/MES', '/MESZ1', 'FX:SME'])
    print(resp)

    # Getting options chains for one equity symbol
    resp = await api.get_options_chain(session_token, 'SPY')
    print(resp)

    # Getting options chains for futures works too
    resp = await api.get_options_chain(session_token, '/MES')
    print(resp)

    """
    ##########
    # ALERTS #
    ##########
    """
    # Create a new quote alert (Last, Bid, Ask, IV and for less than '<' or greater than '>')
    # Note that using 'IV' in the 'field' is actually for 'IV Rank' alert, not pure IV
    # Also works for futures but must be the entire symbol with forward slash and expiration code like '/ESU1'
    alert_json = {
        "field": "Last",
        "operator": ">",
        "threshold": "4200",
        "symbol": "SPX"
    }
    resp = await api.create_quote_alert(session_token, alert_json=alert_json)
    alert_id = resp.get('content').get('data').get('alert-external-id')
    print(resp)

    # Get the quote alerts
    # Returned alerts will include 'completed-at' and 'triggered-at' if they have been triggered
    resp = await api.get_quote_alert(session_token)
    print(resp)

    # Delete an alert using the alert ID
    resp = await api.delete_quote_alert(session_token, alert_id=alert_id)
    print(resp)

    """
    ########
    # MISC #
    ########
    """
    # Retrieve list of all current future products with symbol and product code
    resp = await api.get_instruments_futures(session_token)
    print(resp)

    # Retrieve list of decimal precision for TW available instruments, including crypto
    resp = await api.get_instruments_precisions(session_token)
    print(resp)


if __name__ == '__main__':
    asyncio.run(main())
