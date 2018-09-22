import datetime
import unittest
from decimal import Decimal

from tastyworks.models import option, order, underlying, trading_account


class TestTradingAccount(unittest.TestCase):
    def setUp(self):
        self.order_details = order.OrderDetails(
            type=order.OrderType.LIMIT,
            price=Decimal(400),
            price_effect=order.OrderPriceEffect.CREDIT,
        )
        self.order_details.legs = [
            option.Option(
                ticker='AKS',
                expiry=datetime.date(2018, 8, 31),
                strike=Decimal('3.5'),
                option_type=option.OptionType.CALL,
                underlying_type=underlying.UnderlyingType.EQUITY,
                quantity=1
            )
        ]
        self.test_order = order.Order(self.order_details)

    def test_get_execute_order_json(self):
        res = trading_account._get_execute_order_json(self.test_order)
        expected_result = {
            'source': 'WBT',
            'order-type': 'Limit',
            'price': '400.00',
            'price-effect': 'Credit',
            'time-in-force': 'Day',
            'legs': [
                {
                    'instrument-type': 'Equity Option',
                    'symbol': 'AKS   180831C00003500',
                    'quantity': 1,
                    'action': 'Sell to Open'
                }
            ]
        }

        self.assertDictEqual(res, expected_result)
