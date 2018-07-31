from datetime import date
from enum import Enum

from dataclasses import dataclass


class OptionType(Enum):
    PUT = 'P'
    CALL = 'C'


class OptionUnderlyingType(Enum):
    EQUITY = 'Equity Option'


@dataclass
class Option(object):
    ticker: str
    expiry: date
    strike: float
    option_type: OptionType
    underlying_type: OptionUnderlyingType
    quantity: int = 1

    def get_occ2010_symbol(self):
        strike_int, strike_dec = divmod(self.strike, 1)
        strike_int = int(round(strike_int, 5))
        strike_dec = int(round(strike_dec, 3) * 1000)

        res = '{ticker}{exp_date}{type}{strike_int}{strike_dec}'.format(
            ticker=self.ticker[0:6].ljust(6),
            exp_date=self.expiry.strftime('%y%m%d'),
            type=self.option_type.value,
            strike_int=str(strike_int).zfill(5),
            strike_dec=str(strike_dec).zfill(3)
        )
        return res

    def to_tasty_json(self):
        res = {
            'instrument-type': self.underlying_type.value,
            'symbol': self.get_occ2010_symbol(),
            'quantity': self.quantity
        }
        return res
