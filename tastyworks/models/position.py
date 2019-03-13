from datetime import date, datetime
from decimal import Decimal
from tastyworks.models.alert import Alert, AlertField, Operator
import string
from enum import Enum

from dataclasses import dataclass

class PositionCostEffect(Enum):
    CREDIT = 'Credit'
    DEBIT = 'Debit'
    NONE = None

class InstrumentType(Enum):
    EQUITY_OPTION = 'Equity Option'

class QuantityDirection(Enum):
    LONG = 'Long'
    SHORT = 'Short'

@dataclass
class Position(object):
    account_number: str
    symbol: str
    instrument_type: InstrumentType
    underlying_symbol: str
    quantity: int
    quantity_direction: QuantityDirection
    close_price: Decimal
    average_open_price: Decimal
    average_yearly_market_close_price: Decimal
    mark: Decimal
    mark_price: Decimal
    multiplier: int
    cost_effect: PositionCostEffect
    is_suppressed: bool
    is_frozen: bool
    restricted_quantity: int
    realized_day_gain: Decimal
    realized_day_gain_effect: PositionCostEffect
    realized_day_gain_date: date
    created_at: datetime
    updated_at: datetime

    def get_last_stock_price_alert_oobject(self, Price: Decimal):
        return Alert(alert_field=AlertField('Last'),operator=self.get_alert_operator(),threshold=Price,symbol=self.underlying_symbol)

    def get_alert_operator(self):
        if self.quantity_direction == QuantityDirection.LONG:       # Call
            if self.cost_effect == PositionCostEffect.CREDIT:       # Buy
                return Operator.LESSTHAN
            elif self.cost_effect == PositionCostEffect.DEBIT:      # Sell
                return Operator.GREATERTHAN
        elif self.quantity_direction == QuantityDirection.SHORT:    # Put
            if self.cost_effect == PositionCostEffect.CREDIT:       # Buy
                return Operator.GREATERTHAN
            elif self.cost_effect == PositionCostEffect.DEBIT:      # Sell
                return Operator.LESSTHAN    

    @classmethod
    def from_dict(cls, input_dict: dict):
        """
        Parses a Position object from a dict.
        """
        position = Position(input_dict)
        position.account_number = input_dict['account-number']
        position.symbol = input_dict['symbol']
        position.instrument_type = InstrumentType(input_dict['instrument-type'])
        position.underlying_symbol = input_dict['underlying-symbol']
        position.quantity = int(input_dict['quantity'])
        position.quantity_direction = QuantityDirection(input_dict['quantity-direction'])
        position.close_price = Decimal(input_dict['close-price'])
        position.average_open_price = Decimal(input_dict['average-open-price'])
        position.average_yearly_market_close_price = Decimal(input_dict['average-yearly-market-close-price'])
        position.mark = Decimal(input_dict['mark'])
        position.mark_price = Decimal(input_dict['mark-price'])
        position.multiplier = int(input_dict['multiplier'])
        position.cost_effect = PositionCostEffect(input_dict['cost-effect'])
        position.is_suppressed = bool(input_dict['is-suppressed'])
        position.is_frozen = bool(input_dict['is-frozen'])
        position.restricted_quantity = int(input_dict['restricted-quantity'])
        position.realized_day_gain = Decimal(input_dict['realized-day-gain'])
        position.realized_day_gain_effect = PositionCostEffect(input_dict['realized-day-gain-effect'])
        position.realized_day_gain_date = date(input_dict['realized-day-gain-date'])
        position.created_at = datetime(input_dict['created-at'])
        position.updated_at = datetime(input_dict['updated-at'])
        return cls(position)

    @classmethod
    def list_from_dict(cls, input_dict) -> list:
        ret = []
        for obj in input_dict:
            ret.append(cls.from_dict(obj))
        return ret