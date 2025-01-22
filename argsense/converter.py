import os
import re
import typing as t

from . import config
from .parser.args_parser import ParamType
from .parser.func_parser import T as T0


class T:
    ParamType1 = T0.PlainParamType  # literal
    ParamType2 = ParamType  # enum
    ParamType3 = t.Type  # type
    Style = t.Literal['grp', 'cmd', 'arg', 'opt', 'ext']


def args_2_cargs(*args, **kwargs) -> t.List[str]:
    """
    example:
        args_2_cargs(
            123, 'abc', True, False, None,
            aaa=456, bbb=True, ccc=False, ddd=None, eee='hello'
        )
        -> [
            '123', 'abc', ':true', ':false', ':none', '--aaa', '456', '--bbb',
            '--no-ccc', '--ddd', ':none', '--eee', 'hello'
        ]
    """
    out = []
    for value in args:
        out.append(val_2_cval(value))
    for name, value in kwargs.items():
        out.append(name_2_cname(name, style='opt'))
        if isinstance(value, bool):
            if value is False:
                out[-1] = '--no-' + out[-1][2:]
        else:
            out.append(val_2_cval(value))
    return out


def name_2_cname(name: str, style: T.Style = None) -> str:
    """
    convert param name from python style to cli style.
    
    style   input       output
    -----   ----------  ---------
    arg     aaa_bbb     aaa-bbb
    arg     _aaa_bbb    aaa-bbb
    arg     __aaa_bbb   aaa-bbb
    arg     aaa_bbb_    aaa-bbb
    arg     aaa_bbb__   aaa-bbb
    arg     *aaa_bbb    *aaa-bbb
    opt     aaa_bbb     --aaa-bbb
    opt     _aaa_bbb    --aaa-bbb
    opt     __aaa_bbb   --aaa-bbb  # FIXME: maybe we should not show it in CLI?
    opt     ___aaa_bbb  --aaa-bbb
    opt     aaa_bbb_    --aaa-bbb
    opt     _aaa_bbb_   --aaa-bbb
    opt     **aaa_bbb   **aaa-bbb
    
    other styles follow the same rule with `arg`.
    
    note:
        the output is forced lower case, no matter what the case of `name` is.
    
    warning:
        be careful using `xxx_`, `_xxx`, etc. in the same function. it produces
        duplicate cnames and causes unexpected behavior!
        `./parser/func_parser.py : class FuncInfo : def _register_cname()` will
        raise an error if this happens.
    """
    if name.startswith('*'):
        i = name.rindex('*')
        return name[:i + 1] + name_2_cname(name[i + 1:], style='arg')
    elif name.startswith(':'):
        assert name in (':h', ':help')
        return ':h'
    
    name = name.lower().strip('_')
    if style == 'arg':
        style = config.ARG_NAME_STYLE
        if style == 'AAA_BBB':
            return name.upper()
        elif style == 'AAA-BBB':
            return name.upper().replace('_', '-')
        elif style == 'aaa_bbb':
            return name
        elif style == 'aaa-bbb':  # the default
            return name.replace('_', '-')
        elif style == 'AaaBbb':
            return name.replace('_', ' ').title().replace(' ', '')
        else:
            raise ValueError(f'unknown style: {style}')
    elif style == 'opt':
        return '--' + name.replace('_', '-')
    else:  # follow 'aaa-bbb' style
        return name.replace('_', '-')


def type_2_ctype(t: T.ParamType1) -> T.ParamType2:
    """
    related:
        from: [./parser/func_parser.py : def parse_function()]
        to: [./argparse/parser.py : def parse_sys_argv()]
    """
    return {
        'any'  : ParamType.ANY,
        'bool' : ParamType.BOOL,
        'dict' : ParamType.DICT,
        'flag' : ParamType.FLAG,
        'float': ParamType.NUMBER,
        'int'  : ParamType.NUMBER,
        'list' : ParamType.LIST,
        'none' : ParamType.NONE,
        'set'  : ParamType.LIST,
        'str'  : ParamType.TEXT,
        'tuple': ParamType.LIST,
    }.get(t, ParamType.ANY)


def val_2_cval(value: t.Any, type_: ParamType = ParamType.ANY) -> str:
    """
    FIXME:
        - this function is not stable.
        - this function is not reversible with `cval_2_val()`.
    """
    if value is None:
        return ':none'
    elif value is True:
        return ':true'
    elif value is False:
        return ':false'
    elif value is ...:
        assert type_ == ParamType.ANY
        return '...'
    else:
        if isinstance(value, str):
            if value == '':
                return '""'
            else:
                return value
        if type_ in (ParamType.ANY, ParamType.NUMBER):
            assert isinstance(value, (int, float))
            return str(value)
        elif type_ in (ParamType.BOOL,):
            return ':true' if bool(value) else ':false'
        else:
            raise NotImplementedError(value, type_)


# -----------------------------------------------------------------------------

def cname_2_name(name: str) -> str:
    return name.replace('-', '_')


def ctype_2_type(t: T.ParamType2, v: t.Any = None) -> T.ParamType3:
    if t == ParamType.ANY:
        return str
    elif t == ParamType.BOOL:
        return bool
    elif t == ParamType.FLAG:
        return bool
    elif t == ParamType.NONE:
        return type(None)
    elif t == ParamType.NUMBER:
        if v is None or (isinstance(v, str) and v.isdigit()):
            return int
        return float
    elif t == ParamType.TEXT:
        return str
    else:
        raise NotImplementedError


PYTHON_ACCEPTABLE_NUMBER_PATTERN = re.compile(
    r'^ *-?'
    r'(?:[0-9]+'
    r'|[0-9]*\.[0-9]+'
    r'|0b[01]+'
    r'|0x[0-9a-fA-F]+'
    r') *$'
)

SPECIAL_ARGS = {
    ':cwd'  : os.getcwd(),
    ':empty': '',
    ':f'    : False,
    ':false': False,
    ':h'    : True,
    ':help' : True,
    ':none' : None,
    ':true' : True,
    ':t'    : True,
}


def cval_2_val(value: str, type_: ParamType) -> t.Any:
    # print(':v', arg, type(arg), type, type(type))
    if value in SPECIAL_ARGS:
        return SPECIAL_ARGS[value]
    
    if type_ == ParamType.ANY:
        if PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(value):
            return eval(value)
        else:
            return value
    elif type_ == ParamType.BOOL:
        assert value in (
            ':true', ':false', 'true', 'false', 'TRUE', 'FALSE', '1', '0'
        )
        return True if value in (':true', 'true', 'TRUE', '1') else False
    elif type_ == ParamType.FLAG:
        # raise Exception('unreachable code', value, type_)
        assert value in (
            ':true', ':false', 'true', 'false', 'TRUE', 'FALSE', '1', '0'
        ), ('incorrect value for flag type', value, type_)
        return True if value in (':true', 'true', 'TRUE', '1') else False
    elif type_ == ParamType.NONE:
        assert value in (':none', 'none', 'null', '')
        return None
    elif type_ == ParamType.NUMBER:
        assert PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(value)
        return eval(value)
    elif type_ == ParamType.TEXT:
        return value
    else:
        raise NotImplementedError(value, type_)
