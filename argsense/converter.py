import typing as t

from .argparse import ParamType

__all__ = ['name_2_cname', 'type_2_ctype']


class T:
    from .parser.func_parser import TParamType as _ParamType
    ParamType1 = _ParamType
    ParamType2 = ParamType
    Style = t.Literal['grp', 'cmd', 'arg', 'opt', 'ext']


def name_2_cname(name: str, style: T.Style = None) -> str:
    # convert name from snake_case to kebab-case.
    name = name.lower().lstrip('_').replace('_', '-')
    if style == 'arg':
        # # name = name.upper()
        name = name.replace('-', '_').upper()
    elif style == 'opt':
        name = '--' + name
    return name


def type_2_ctype(t: T.ParamType1) -> T.ParamType2:
    return {
        'str'  : ParamType.TEXT,
        'int'  : ParamType.NUMBER,
        'float': ParamType.NUMBER,
        'bool' : ParamType.FLAG,
        # 'list' : ParamType.LIST,
        # 'tuple': ParamType.LIST,
        # 'set'  : ParamType.LIST,
        # 'dict' : ParamType.DICT,
        'any'  : ParamType.ANY,
        # 'none' : ParamType.NONE,
    }.get(t, ParamType.ANY)
