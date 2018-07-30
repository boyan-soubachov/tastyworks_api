from enum import Enum

from tastyworks.models.model import Model


class OptionType(Enum):
    PUT = 'put'
    CALL = 'call'


class Option(Model):
    pass
