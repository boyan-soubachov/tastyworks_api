import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict

import aiohttp

from tastyworks.models.option import Option, OptionType
from tastyworks.models.underlying import Underlying, UnderlyingType

LOGGER = logging.getLogger(__name__)


class OptionChain(object):
    """
    Maps option symbols to Option structures
    Provides filter methods based on type, strike price, expiry, etc.

    Example usage:
        symbol = "AAPL"
        response = await client.get_option_chains(symbol)
        oc = OptionChain(OptionChain.parse(symbol, response))

        for strike in oc.get_all_strikes():
            print(strike)

        for expiry in oc.get_all_expirations():
            print(expiry)

        for symbol, option in oc.get(strike=300.0,option_type=OptionType.CALL,expiry=datetime.date(2018,9,21)).items():
            print(symbol, option)
    """

    def __init__(self, options):
        self.options = options

    def _get_filter_strategy(self, key, unique=True):
        values = [getattr(option, key) for option in self.options]
        if not any(values):
            raise Exception(f'No values found for specified key: {key}')

        values = list(set(values)) if unique else list(values)
        return sorted(values)

    def get_all_strikes(self):
        return self._get_filter_strategy('strike')

    def get_all_expirations(self):
        return self._get_filter_strategy('expiry')


async def get_option_chain(session, underlying: Underlying, expiration: date = None) -> OptionChain:
    LOGGER.debug('Getting options chain for ticker: %s', underlying.ticker)
    data = await _get_tasty_option_chain_data(session, underlying)
    res = []

    for exp in data['expirations']:
        exp_date = datetime.strptime(exp['expiration-date'], '%Y-%m-%d').date()

        if expiration and expiration != exp_date:
            continue

        for strike in exp['strikes']:
            strike_val = Decimal(strike['strike-price'])
            for option_types in OptionType:
                new_option = Option(
                    ticker=underlying.ticker,
                    expiry=exp_date,
                    strike=strike_val,
                    option_type=option_types,
                    underlying_type=UnderlyingType.EQUITY
                )
                res.append(new_option)
    return OptionChain(res)


async def _get_tasty_option_chain_data(session, underlying) -> Dict:
    async with aiohttp.request(
            'GET',
            f'{session.API_url}/option-chains/{underlying.ticker}/nested',
            headers=session.get_request_headers()) as response:

        if response.status != 200:
            raise Exception(f'Could not find option chain for symbol {underlying.ticker}')
        resp = await response.json()

        # NOTE: Have not seen an example with more than 1 item. No idea what that would be.
        return resp['data']['items'][0]
