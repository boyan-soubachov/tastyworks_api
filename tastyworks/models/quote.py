from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


# {'eventSymbol': 'SPY',
#  'eventTime': datetime.datetime(1969, 12, 31, 16, 0),
#  'sequence': 0,
#  'timeNanoPart': 0,
#  'bidTime': datetime.datetime(1969, 12, 31, 16, 0),
#  'bidExchangeCode': 'P',
#  'bidPrice': 415.72,
#  'bidSize': 5.0,
#  'askTime': datetime.datetime(1969, 12, 31, 16, 0),
#  'askExchangeCode': 'P',
#  'askPrice': 415.78,
#  'askSize': 9.0}

# {'eventSymbol': '.SPY210419P408',
#  'eventTime': datetime.datetime(1969, 12, 31, 16, 0),
#  'sequence': 0,
#  'timeNanoPart': 0,
#  'bidTime': datetime.datetime(1969, 12, 31, 16, 0),
#  'bidExchangeCode': 'J',
#  'bidPrice': 0.0,
#  'bidSize': 0.0,
#  'askTime': datetime.datetime(1969, 12, 31, 16, 0),
#  'askExchangeCode': 'X',
#  'askPrice': 0.01,
#  'askSize': 4947.0}


@dataclass
class Quote(object):
    symbol: str
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    datetime: datetime

    def __init__(self, input_dict: dict):
        """
        Store the Quote data from a dictionary pulled from subscribed data
            sub_values = {"Quote": ["SPY"]}
            await streamer.add_data_sub(sub_values)
        Args:
            input_dict: dictionary containing the quote data for one symbol
        """
        self.symbol = input_dict['eventSymbol']
        self.bid_price = input_dict['bidPrice']
        self.ask_price = input_dict['askPrice']
        self.bid_size = input_dict['bidSize']
        self.ask_size = input_dict['askSize']
        self.datetime = datetime.now()
