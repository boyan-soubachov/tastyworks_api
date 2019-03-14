from datetime import date, datetime
from decimal import Decimal
from tastyworks.models.alert import Alert, AlertField, Operator
from tastyworks.models.order import (Order, OrderDetails, OrderPriceEffect, OrderType)
from tastyworks.models.option import Option, OptionType
from tastyworks.models.underlying import UnderlyingType
from enum import Enum
from dataclasses import dataclass


class PositionCostEffect(Enum):
    CREDIT = 'Credit'
    DEBIT = 'Debit'
    NONE = 'None'


class InstrumentType(Enum):
    EQUITY_OPTION = 'Equity Option'
    NONE = None


class QuantityDirection(Enum):
    LONG = 'Long'
    SHORT = 'Short'
    NONE = None


@dataclass
class Position(object):
    account_number: str = None
    symbol: str = None
    instrument_type: InstrumentType = InstrumentType.NONE
    underlying_symbol: str = None
    quantity: int = None
    quantity_direction: QuantityDirection = QuantityDirection.NONE
    close_price: Decimal = None
    average_open_price: Decimal = None
    average_yearly_market_close_price: Decimal = None
    mark: Decimal = None
    mark_price: Decimal = None
    multiplier: int = 100
    cost_effect: PositionCostEffect = PositionCostEffect.NONE
    is_suppressed: bool = None
    is_frozen: bool = None
    restricted_quantity: int = 0
    realized_day_gain: Decimal = None
    realized_day_gain_effect: PositionCostEffect = PositionCostEffect.NONE
    realized_day_gain_date: date = None
    created_at: datetime = None
    updated_at: datetime = None

    def is_option(self):
        if self.instrument_type == InstrumentType.EQUITY_OPTION:
            return True
        else:
            return False

    def get_option_obj(self):
        exp_date = datetime.strptime(self.symbol[6:12], '%y%m%d').date()
        option_type = OptionType(self.symbol[12:13])
        strike = Decimal(self.symbol[13:]) / 1000
        return Option(ticker=self.underlying_symbol, quantity=self.quantity, expiry=exp_date, strike=strike, option_type=option_type, underlying_type=UnderlyingType.EQUITY)

    def get_closing_order_price_effect(self):
        if self.cost_effect == PositionCostEffect.CREDIT:
            return OrderPriceEffect.CREDIT
        elif self.cost_effect == PositionCostEffect.DEBIT:
            return OrderPriceEffect.DEBIT

    def get_closing_order_object(self, price: Decimal, stop_trigger: Decimal = None, order_type: OrderType = OrderType.LIMIT):
        closing_order_price_effect = self.get_closing_order_price_effect()
        details = OrderDetails(type=order_type, price=price, price_effect=closing_order_price_effect, stop_trigger=stop_trigger)
        new_order = Order(details)
        opt = self.get_option_obj()
        new_order.add_leg(opt)
        return new_order

    def get_last_stock_price_alert_oobject(self, Price: Decimal):
        return Alert(alert_field=AlertField('Last'), operator=self.get_alert_operator(), threshold=Price, symbol=self.underlying_symbol)

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
        position = cls(input_dict)
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
        position.realized_day_gain_date = datetime.strptime(input_dict['realized-day-gain-date'], '%Y-%m-%d').date()
        position.created_at = datetime.strptime(input_dict['created-at'].split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
        position.updated_at = datetime.strptime(input_dict['updated-at'].split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
        return position

    @classmethod
    def list_from_dict(cls, input_dict) -> list:
        ret = []
        for obj in input_dict:
            ret.append(cls.from_dict(obj))
        return ret
