from dataclasses import dataclass
from decimal import Decimal

# [{'eventSymbol': '.SPY210419P410',
#   'eventTime': 0,
#   'eventFlags': 0,
#   'index': 6951999236862902272,
#   'time': 1618638457000,
#   'sequence': 0,
#   'price': 0.07332271,
#   'volatility': 0.09516809,
#   'delta': -0.04395782,
#   'gamma': 0.02291552,
#   'theta': -0.04936977,
#   'rho': -0.00192595,
#   'vega': 0.03967128}]


@dataclass
class Greeks(object):
    symbol: str
    # time: datetime
    price: Decimal
    volatility: Decimal
    delta: Decimal
    gamma: Decimal
    theta: Decimal
    rho: Decimal
    vega: Decimal

    def __init__(self, input_dict: dict):
        """
        imports the Greeks data from a dictionary pulled from subscribed data
            sub_greeks = {"Greeks": [".SPY210419P410"]}
            await streamer.add_data_sub(sub_greeks)
        Args:
            input_dict: dictionary containing the greeks data
        """
        self.symbol = input_dict['eventSymbol']
        self.price = input_dict['price']
        self.volatility = input_dict['volatility']
        self.delta = input_dict['delta']
        self.gamma = input_dict['gamma']
        self.theta = input_dict['theta']
        self.rho = input_dict['rho']
        self.vega = input_dict['vega']
