import logging
from decimal import Decimal
from enum import Enum

from dataclasses import dataclass, field

class Field(Enum):
    LAST = 'Last'
    BID = 'Bid'
    ASK = 'Ask'
    IVX = 'IVx'

class Operator(Enum):
    LESSTHAN = '<'
    GREATERTHAN = '>'

@dataclass
class Alert:
    field: Field
    operator: Operator
    symbol: str = ticker
    threshold: Decimal = Decimal(price)

    @classmethod
    def get_json(self):
        alert_json = {
        'field': self.field.value,
        'operator': self.operator.value,
        'threshold': '{:.3f}'.format(self.threshold),
        'symbol': self.symbol
        }
        return alert_json

def from_dict(self, data):
    ret = []
    for item in data:
        ret.append(Alert(field=item['field'],
              operator=item['operator'],
              threshold=item['threshold'],
              symbol=item['symbol']))
    return ret