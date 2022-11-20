from __future__ import annotations

import typing as t

from . import config
from .argparse import ParamType
from .parser.func_parser import T as T0


class T:
    ParamType1 = T0.ParamType
    ParamType2 = ParamType
    Style = t.Literal['grp', 'cmd', 'arg', 'opt', 'ext']


def args_2_cargs(*args, **kwargs) -> list[str]:
    """
    example:
        args_2_cargs(
            123, 'abc', True, False, None,
            aaa=456, bbb=True, ccc=False, ddd=None, eee='hello')
        -> ['123', 'abc', ':true', ':false', ':none', '--aaa', '456', '--bbb',
            '--not-ccc', '--ddd', ':none', '--eee', 'hello']
    """
    def value_2_cvalue(value: t.Any) -> str:
        if value is None:
            return ':none'
        elif value is True:
            return ':true'
        elif value is False:
            return ':false'
        else:
            return str(value)
        
    out = []
    for value in args:
        out.append(value_2_cvalue(value))
    for name, value in kwargs.items():
        out.append(name_2_cname(name, style='opt'))
        if isinstance(value, bool):
            if value is False:
                out[-1] = '--not-' + out[-1][2:]
        else:
            out.append(value_2_cvalue(value))
    return out


def name_2_cname(name: str, style: T.Style = None) -> str:
    """ convert param name from python style to cli style. """
    if name in ('*', '**'):
        return name
    name = name.lower().strip('_')
    if style == 'arg':
        style = config.ARG_NAME_STYLE
        if style == 'AAA_BBB':
            return name.upper()
        elif style == 'AAA-BBB':
            return name.upper().replace('_', '-')
        elif style == 'aaa_bbb':
            return name
        elif style == 'aaa-bbb':
            return name.replace('_', '-')
        elif style == 'AaaBbb':
            return name.replace('_', ' ').title().replace(' ', '')
        else:
            raise ValueError(f'unknown style: {style}')
    elif style == 'opt':
        return '--' + name.replace('_', '-')
    else:
        return name.replace('_', '-')


def type_2_ctype(t: T.ParamType1) -> T.ParamType2:
    """
    related:
        from: [./parser/func_parser.py : def parse_function()]
        to: [./argparse/parser.py : def parse_argv()]
    """
    return {
        'any'  : ParamType.ANY,
        'str'  : ParamType.TEXT,
        'float': ParamType.NUMBER,
        'flag' : ParamType.FLAG,
        'bool' : ParamType.BOOL,
        'int'  : ParamType.NUMBER,
        'list' : ParamType.LIST,
        'tuple': ParamType.LIST,
        'set'  : ParamType.LIST,
        'dict' : ParamType.DICT,
        'none' : ParamType.NONE,
    }.get(t, ParamType.ANY)
