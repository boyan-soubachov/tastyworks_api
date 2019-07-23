from dataclasses import dataclass, field
from typing import List
from enum import Enum
from datetime import datetime
from .account import *

class AccountEventType(Enum):
    ACTION = 'action'
    CHANGE = 'type'

class ActionAccountEventType(Enum):
    HEARTBEAT = 'heartbeat'
    ACCOUNT_SUBSCRIBE = 'account-subscribe'

    @classmethod
    def from_str(cls, str_rep):
       return (ActionAccountEventType.HEARTBEAT
               if str_rep == ActionAccountEventType.HEARTBEAT.value
               else ActionAccountEventType.ACCOUNT_SUBSCRIBE
               if str_rep == ActionAccountEventType.ACCOUNT_SUBSCRIBE.value
               else None)

class ChangeAccountEventType(Enum):
    ORDER = 'Order'
    ACOUNT_BALANCE = 'AccountBalance'
    CURRENT_POSITION = 'CurrentPosition'
    TRADING_STATUS = 'TradingStatus'

    @classmethod
    def from_str(cls, str_rep):
        return (ChangeAccountEventType.ORDER
                if str_rep == ChangeAccountEventType.ORDER.value
                else ChangeAccountEventType.CURRENT_POSITION
                if str_rep == ChangeAccountEventType.CURRENT_POSITION.value
                else ChangeAccountEventType.TRADING_STATUS
                if str_rep == ChangeAccountEventType.TRADING_STATUS.value
                else ChangeAccountEventType.ACOUNT_BALANCE
                if str_rep == ChangeAccountEventType.ACOUNT_BALANCE.value
                else None)

class AccountEvent(object):
    @staticmethod
    def detect_type(input_dict:dict) -> AccountEventType:
        if AccountEventType.ACTION.value in input_dict:
            return ActionAccountEvent
        elif AccountEventType.CHANGE.value in input_dict:
            return ChangeAccountEvent        
        raise TypeError("Unknown Account Event type")

    @classmethod
    def from_dict(cls, input_dict:dict) -> AccountEventType:
        input_dict = {k.replace("-","_"): v for k,v in input_dict.items()}
        return cls.detect_type(input_dict)(**input_dict)

@dataclass
class ActionAccountEvent(AccountEvent):
    action: str
    action_enum: ActionAccountEventType = field(init=False, repr=False)
    request_id: str = None
    auth_token: str = None
    message: str = None
    value: List[str] = None

    def __post_init__(self):
        self.action_enum = ActionAccountEventType.from_str(self.action)

@dataclass
class ChangeAccountEvent(AccountEvent):
    type: str
    type_enum: ChangeAccountEventType = field(init=False, repr=False)
    data: dict = field(repr=False)
    data_obj: ChangeAccountObject = field(init=False, repr=False)
    timestamp: float = field(repr=False)
    timestamp_formatted: str = field(init=False)

    def __post_init__(self):
        self.type_enum = ChangeAccountEventType.from_str(self.type)
        self.timestamp_formatted = str(datetime.fromtimestamp(self.timestamp/1000))

        if self.type_enum == ChangeAccountEventType.ORDER:
            self.data_obj = OrderChangeAccountObject(**from_tasty_dict(self.data))
