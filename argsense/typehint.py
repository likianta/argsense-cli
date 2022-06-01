from enum import Enum
from typing import *

__all__ = [
    # custom
    'FuncInfo',
    'OptionsInfo',
    'ParamType',
    'ParamsInfo',
    # builtin
    'Any',
    'Callable',
    'Dict',
    'List',
    'Sequence',
    'Tuple',
    'Union',
]

# -----------------------------------------------------------------------------

_ArgName = str  # C1
_ArgType = Literal[  # C2
    'any', 'bool', 'bytes', 'dict', 'float', 'int',
    'list', 'none', 'set', 'str', 'tuple'
]
_DefaultValue = Any  # C3

_Args = List[Tuple[_ArgName, _ArgType]]  # B1
_KwArgs = List[Tuple[_ArgName, _ArgType, _DefaultValue]]  # B2

FuncInfo = TypedDict('FuncInfo', {  # A1
    'name'  : str,
    'args'  : _Args,
    'kwargs': _KwArgs,
    'return': _ArgType,
})

# -----------------------------------------------------------------------------

_KwArgName = str
_OptionName = str
_ParamName = str


class ParamType(Enum):
    TEXT = 'text'
    NUMBER = 'number'
    FLAG = 'flag'
    ANY = 'any'


ParamsInfo = TypedDict('ParamsInfo', {
    'args': Dict[_ParamName, ParamType],
    'kwargs': Dict[_KwArgName, ParamType],
    'index': Dict[_OptionName, _KwArgName],
})

OptionsInfo = TypedDict('OptionsInfo', {  # DELETE
    'index'         : Dict[_KwArgName, TypedDict('ParamInfo', {
        'option' : Sequence[_OptionName],
        'type'   : Literal['text', 'number', 'flag', 'any'],
        'default': Any,
    })],
    'reversed_index': Dict[_OptionName, _KwArgName],
})
''' {
        'index': {
            str kwarg_name: {
                'option': union[list, tuple] option_names,
                    option_names:
                        the type is list or tuple.
                        by default its length is 1. for example:
                            {'some_option': ['--some-option'], ...}
                        but if user has additionally defined custom name, the
                        length will be more than 1. for example:
                            {'some_option': ['--some-option', '-o'], ...}
                        be noticed if name duplicated happens, an error will be
                        raised.
                'type': literal type,
                    type: literal['text', 'number', 'flag', 'any']
                'default': any,
            }, ...
        },
        'reversed_index': {
            str option_name: str kwarg_name, ...
        }
    }
'''
