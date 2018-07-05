# TODO: Convert this to a dataclass when python 3.7 comes out on APT
from dataclasses import dataclass


@dataclass
class TradingAccount(object):
    account_number: str
    external_id: str
    is_margin: bool
