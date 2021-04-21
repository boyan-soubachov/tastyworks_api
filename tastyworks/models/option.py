from datetime import date
from decimal import Decimal
from enum import Enum

from dataclasses import dataclass

from tastyworks.models.security import Security
from tastyworks.models.underlying import UnderlyingType
from tastyworks.models.greeks import Greeks


class OptionType(Enum):
    PUT = 'P'
    CALL = 'C'


class ExpirationType(Enum):
    WEEKLY = 'Weekly'
    REGULAR = 'Regular'
    QUARTERLY = 'Quarterly'


class SettlementType(Enum):
    AM = 'AM'
    PM = 'PM'


@dataclass
class Option(Security):
    symbol: str
    ticker: str
    expiration_date: date
    dte: int
    strike: Decimal
    option_type: OptionType
    underlying_type: UnderlyingType
    shares_per_contract: int
    expiration_type: str
    settlement_type: str
    greeks: Greeks
    # quote: Quote
    #quantity: int = 1

    def _get_underlying_type_string(self, underlying_type: UnderlyingType):
        if underlying_type == UnderlyingType.EQUITY:
            return 'Equity Option'

    def get_occ2010_symbol(self):
        strike_int, strike_dec = divmod(self.strike, 1)
        strike_int = int(round(strike_int, 5))
        strike_dec = int(round(strike_dec, 3) * 1000)

        res = '{ticker}{exp_date}{type}{strike_int}{strike_dec}'.format(
            ticker=self.ticker[0:6].ljust(6),
            exp_date=self.expiration_date.strftime('%y%m%d'),
            type=self.option_type.value,
            strike_int=str(strike_int).zfill(5),
            strike_dec=str(strike_dec).zfill(3)
        )
        return res

    def get_dxfeed_symbol(self):
        if self.strike % 1 == 0:
            strike_str = '{0:.0f}'.format(self.strike)
        else:
            strike_str = '{0:.2f}'.format(self.strike)
            if strike_str[-1] == '0':
                strike_str = strike_str[:-1]

        res = '.{ticker}{exp_date}{type}{strike}'.format(
            ticker=self.ticker,
            exp_date=self.expiration_date.strftime('%y%m%d'),
            type=self.option_type.value,
            strike=strike_str
        )
        self.symbol = res
        return res

    def to_tasty_json(self):
        res = {
            'instrument-type': f'{self.underlying_type.value} Option',
            'symbol': self.get_occ2010_symbol(),
            'quantity': self.quantity
        }
        return res
