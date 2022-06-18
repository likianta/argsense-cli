from enum import Enum
from enum import auto


# noinspection PyArgumentList
class ParamType(Enum):
    TEXT = auto()
    NUMBER = auto()
    FLAG = auto()
    BOOL = auto()
    ANY = auto()
