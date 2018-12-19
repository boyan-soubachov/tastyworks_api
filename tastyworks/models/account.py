from dataclasses import dataclass, field
from typing import List
from datetime import datetime

from .order import OrderType, OrderPriceEffect, OrderStatus

def from_tasty_dict(tasty_dict:dict) -> dict:
    return {key.replace('-','_'):value for key,value in tasty_dict.items()}
def to_tasty_dict(my_dict:dict) -> dict:
    return {key.replace('_','-'):value for key,value in my_dict.items()}

@dataclass
class ChangeAccountObject(object):
    account_number: str

@dataclass
class FillAccountObject(object):
    ext_group_fill_id: str
    ext_exec_id: str
    quantity: int
    fill_price: float
    filled_at: str

@dataclass
class LegAccountObject(object):
    instrument_type: str
    symbol: str
    quantity: int
    remaining_quantity: int
    action: str
    fills: List[FillAccountObject]

    def __post_init__(self):
        if self.fills:
            self.fills = [FillAccountObject(**from_tasty_dict(fill)) for fill in self.fills]

@dataclass
class OrderChangeAccountObject(ChangeAccountObject):
    id: float
    time_in_force: str
    order_type: OrderType
    size: int
    underlying_symbol: str
    status: str
    status_enum: OrderStatus = field(init=False, repr=False)  
    cancellable: bool = field(repr=False)    
    editable: bool = field(repr=False)
    edited: bool = field(repr=False)
    received_at: str = field(repr=False)
    updated_at: float = field(repr=False)
    updated_at_formatted: str = field(init=False, repr=False)
    legs: List[LegAccountObject]

    price: float = field(default=None)
    price_effect: str = field(default=None)         #Doesn't come on a Stop Market order
    price_effect_enum: OrderPriceEffect = field(init=False, repr=False)
    cancelled_at: str = field(repr=False, default=None)
    terminal_at: str = field(repr=False, default=None)
    stop_trigger: float = field(repr=False, default=None)
    reject_reason: str = field(repr=False, default=None)
    ext_exchange_order_number: str = field(repr=False, default=None)
    ext_client_order_id: str = field(repr=False, default=None)
    ext_global_order_number: float = field(repr=False, default=None)
     
    def __post_init__(self):
        if self.price:
            self.price = float(self.price)
        if self.price_effect:
            self.price_effect_enum = OrderPriceEffect.from_str(self.price_effect)
        self.status_enum = OrderStatus.from_str(self.status)
        if self.stop_trigger:
            self.stop_trigger = float(self.stop_trigger)
        self.updated_at_formatted = str(datetime.fromtimestamp(self.updated_at/1000))
        if self.legs:
           self.legs = [LegAccountObject(**from_tasty_dict(leg)) for leg in self.legs]

    def is_open_order(self):

        is_open = False
        for leg in self.legs:
            if "Buy" in leg.action:
                is_open = True
                break
        return is_open