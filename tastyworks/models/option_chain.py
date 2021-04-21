import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict

import aiohttp

from tastyworks.models.option import Option, OptionType
from tastyworks.models.underlying import Underlying, UnderlyingType
from tastyworks.models.greeks import Greeks

LOGGER = logging.getLogger(__name__)


class OptionChain(object):
    """
    Maps option symbols to Option structures
    Provides filter methods based on type, strike price, expiration_date, etc.

    Example usage:
        symbol = "AAPL"
        response = await client.get_option_chains(symbol)
        oc = OptionChain(OptionChain.parse(symbol, response))

        for strike in oc.get_all_strikes():
            print(strike)

        for expiration_date in oc.get_all_expirations():
            print(expiration_date)

        for symbol, option in oc.get(strike=300.0,option_type=OptionType.CALL,expiration_date=datetime.date(2018,9,21)).items():
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
        return self._get_filter_strategy('expiration_date')


async def get_option_chain(session, underlying: Underlying, expiration: date = None) -> OptionChain:
    LOGGER.info('Getting options chain for ticker: %s', underlying.ticker)
    data = await _get_tasty_option_chain_data(session, underlying)
    # {'underlying-symbol': 'SPY',
    #  'root-symbol': 'SPY',
    #  'option-chain-type': 'Standard',
    #  'shares-per-contract': 100,
    #  'tick-sizes': [{'value': '0.01'}],
    #  'deliverables': [{'id': 70795,
    #                    'root-symbol': 'SPY',
    #                    'deliverable-type': 'Shares',
    #                    'description': '100 shares of SPY',
    #                    'amount': '100.0',
    #                    'symbol': 'SPY',
    #                    'instrument-type': 'Equity',
    #                    'percent': '100'}],
    #  'expirations': [{'expiration-type': 'Weekly',
    #                   'expiration-date': '2021-04-19',
    #                   'days-to-expiration': 1,
    #                   'settlement-type': 'PM',
    #                   'strikes': [{'strike-price': '250.0', 'call': 'SPY   210419C00250000', 'put': 'SPY   210419P00250000'},
    #                               {'strike-price': '255.0', 'call': 'SPY   210419C00255000', 'put': 'SPY   210419P00255000'},
    #                               {'strike-price': '260.0', 'call': 'SPY   210419C00260000', 'put': 'SPY   210419P00260000'},
    #                               {'strike-price': '265.0', 'call': 'SPY   210419C00265000', 'put': 'SPY   210419P00265000'},....
    res = []

    for exp in data['expirations']:
        exp_date = datetime.strptime(exp['expiration-date'], '%Y-%m-%d').date()

        if expiration and expiration != exp_date:
            continue

        for strike in exp['strikes']:
            strike_val = Decimal(strike['strike-price'])
            for option_types in OptionType:
                new_option = Option(
                    symbol='',
                    ticker=underlying.ticker,
                    expiration_date=exp_date,
                    dte=int(exp['days-to-expiration']),
                    strike=strike_val,
                    option_type=option_types,
                    underlying_type=UnderlyingType.EQUITY,
                    shares_per_contract=data['shares-per-contract'],
                    expiration_type=exp['expiration-type'],
                    settlement_type=exp['settlement-type'],
                    greeks=Greeks
                )
                res.append(new_option)
    return OptionChain(res)


async def _get_tasty_option_chain_data(session, underlying) -> Dict:
    """
    https://api.tastyworks.com/option-chains/SPY/nested
    Args:
        session:
        underlying:

    Returns:

    """
    async with aiohttp.request(
            'GET',
            f'{session.API_url}/option-chains/{underlying.ticker}/nested',
            headers=session.get_request_headers()) as response:

        if response.status != 200:
            raise Exception('Could not find option chain for symbol', underlying.ticker)
        resp = await response.json()

        # NOTE: Have not seen an example with more than 1 item. No idea what that would be.
        return resp['data']['items'][0]
