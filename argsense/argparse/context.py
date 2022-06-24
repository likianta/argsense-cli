from enum import Enum
from enum import auto

from .params import ParamType


# noinspection PyArgumentList
class Token(Enum):
    START = auto()
    READY = auto()
    OPTION_NAME = auto()


class Context:
    last_last_token: Token = None
    last_token: Token = None
    token: Token = None
    
    param_name: str
    param_type: ParamType
    
    last_last_arg: str = None
    last_arg: str = None
    arg: str = None
    
    def __init__(self):
        self.token = Token.START
    
    def update(self, token: Token):
        self.last_last_token = self.last_token
        self.last_token = self.token
        self.token = token
    
    def store_param_info(self, name: str, type_: ParamType):
        self.param_name = name
        self.param_type = type_
