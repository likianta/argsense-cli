"""
here are stored shared type hints across multiple modules.
"""
import typing as t
from enum import EnumType


class T:
    # noinspection PyTypedDict
    FuncInfo = t.TypedDict('FuncInfo', {
        'func'          : t.Callable,
        'cname'         : str,
        'desc'          : str,
        'args'          : t.Dict[
            str, t.TypedDict('ArgInfo', {
                'cname': str,
                'ctype': EnumType,
                'desc' : str,
            })
        ],
        'kwargs'        : t.Dict[
            str, t.TypedDict('ArgInfo', {
                'cname'  : str,
                'ctype'  : EnumType,
                'desc'   : str,
                'default': t.Any,
            })
        ],
        'transport_help': bool
    })
    
    # be noticed this should not be an iterator type, because we may use it
    # many times.
    FuncsInfo = t.Union[t.Tuple[FuncInfo, ...], t.List[FuncInfo]]
