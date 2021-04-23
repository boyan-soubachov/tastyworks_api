import unittest
from tastyworks.models import greeks

dict_input = {
            'eventSymbol': '.SPY210419P410',
            'eventTime': 0,
            'eventFlags': 0,
            'index': 6951999236862902272,
            'time': 1618638457000,
            'sequence': 0,
            'price': 0.07332271,
            'volatility': 0.09516809,
            'delta': -0.04395782,
            'gamma': 0.02291552,
            'theta': -0.04936977,
            'rho': -0.00192595,
            'vega': 0.03967128
        }


class TestGreeksModel(unittest.TestCase):
    def setUp(self):
        pass

    def test_from_dict(self):
        gr = greeks.Greeks()
        gr.from_dict(dict_input)
        self.assertEqual(gr, gr)
