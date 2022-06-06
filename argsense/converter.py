import typing as t
from .argparse import ParamType as ParamType2
from .parser.func_parser import TParamType as ParamType1

__all__ = ['name_2_cname', 'type_2_ctype']


class T:
    PresetStyle = t.Literal['grp', 'cmd', 'arg', 'opt', 'ext']


def name_2_cname(name: str, style: T.PresetStyle = None) -> str:
    # convert name from snake_case to kebab-case.
    name = name.lstrip('_').replace('_', '-')
    if style == 'arg':
        name = name.upper()
    elif style == 'opt':
        name = '--' + name
    return name


def type_2_ctype(t: ParamType1) -> ParamType2:
    return {
        'str'  : ParamType2.TEXT,
        'int'  : ParamType2.NUMBER,
        'float': ParamType2.NUMBER,
        'bool' : ParamType2.FLAG,
        # 'list' : ParamType2.LIST,
        # 'tuple': ParamType2.LIST,
        # 'set'  : ParamType2.LIST,
        # 'dict' : ParamType2.DICT,
        'any'  : ParamType2.ANY,
        # 'none' : ParamType2.NONE,
    }.get(t, ParamType2.ANY)
