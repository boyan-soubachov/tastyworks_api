import logging
from decimal import Decimal
from enum import Enum

from dataclasses import dataclass

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
    symbol: str
    threshold: Decimal

    @classmethod
    def get_json(self):
        alert_json = {
        'field': self.field.value,
        'operator': self.operator.value,
        'threshold': '{:.3f}'.format(self.threshold),
        'symbol': self.symbol
        }
        return alert_json

def alert_from_dict(data: dict):
    ret = []
    for item in data:
        ret.append(Alert(field=Field(item['field']),
            operator=Operator(item['operator']),
            threshold=Decimal(item['threshold']),
            symbol=item['symbol']))
    return ret