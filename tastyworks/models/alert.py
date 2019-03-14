from decimal import Decimal
from enum import Enum
from datetime import datetime
from dataclasses import dataclass


class AlertField(Enum):
    LAST = 'Last'
    BID = 'Bid'
    ASK = 'Ask'
    IVX = 'IV'


class Operator(Enum):
    LESSTHAN = '<'
    GREATERTHAN = '>'


@dataclass
class Alert:
    alert_field: AlertField
    operator: Operator
    symbol: str
    threshold: Decimal
    alert_external_id: str = ''
    user_external_id: str = ''
    triggered_at: datetime = None
    triggered: bool = False

    def get_json(self):
        alert_json = {'field': self.alert_field.value,
                      'operator': self.operator.value,
                      'threshold': '{:.3f}'.format(self.threshold),
                      'symbol': self.symbol
                      }
        return alert_json

    @staticmethod
    def from_dict(data: dict):
        ret = []
        for item in data:
            alert = Alert(alert_field=AlertField(item['field']),
                             operator=Operator(item['operator']),
                             threshold=Decimal(item['threshold']),
                             symbol=item['symbol'],
                             user_external_id=item['user-external-id'],
                             alert_external_id=item['alert-external-id'])
            if 'triggered-at' in item:
                alert.triggered_at = datetime.strptime(item['triggered-at'].split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
                if datetime.utcnow() > alert.triggered_at:
                    alert.triggered = True
            ret.append(alert)
        return ret
