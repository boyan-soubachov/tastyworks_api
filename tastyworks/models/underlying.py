from enum import Enum

from tastyworks.models.security import Security


class UnderlyingType(Enum):
    EQUITY = 'Equity'


class Underlying(Security):
    def __init__(self, ticker=None):
        self.ticker = ticker
