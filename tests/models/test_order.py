import unittest
from tastyworks.models import order


class TestOrderStatus(unittest.TestCase):
    def setUp(self):
        self.json_input = {
            'underlying-symbol': 'NUGT',
            'price': '1.4213',
            'price-effect': 'Credit',
            'order-type': 'Market',
            'status': 'Rejected',
            'time-in-force': 'Day',
        }

    def test_from_dict_no_price(self):
        del self.json_input['price']
        res = order.Order.from_dict(self.json_input)
        self.assertEqual(res.details.type, order.OrderType.MARKET)
        self.assertIsNone(res.details.price)
