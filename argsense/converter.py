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
    """
    convert param name from python style to cli style.
    
    style   input       output
    -----   ----------  ---------
    arg     aaa_bbb     aaa-bbb
    arg     _aaa_bbb    aaa-bbb
    arg     __aaa_bbb   aaa-bbb
    arg     aaa_bbb_    aaa-bbb
    arg     aaa_bbb__   aaa-bbb
    opt     aaa_bbb     --aaa-bbb
    opt     _aaa_bbb    --aaa-bbb
    opt     __aaa_bbb   --aaa-bbb  # FIXME: maybe we should not show it in CLI?
    opt     ___aaa_bbb  --aaa-bbb
    opt     aaa_bbb_    --aaa-bbb
    opt     _aaa_bbb_   --aaa-bbb
    
    other styles follow the same rule with `arg`.
    
    note:
        the output is forced lower case, no matter what the case of `name` is.
    
    warning:
        be careful using `xxx_`, `_xxx`, etc. in the same function. it produces
        duplicate cnames and causes unexpected behavior!
        `./parser/func_parser.py : class FuncInfo : def _append_cname()` will
        raise an error if this happens.
    """
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


def val_2_str(value: t.Any, type_: ParamType) -> str:
    assert type_ not in (ParamType.DICT, ParamType.LIST), (
        'the complex type is not implemented', type_
    )
    conv = {
        None : ':none',
        True : ':true',
        False: ':false',
    }
    if value in conv:
        return conv[value]
    else:
        return str(value)


# -----------------------------------------------------------------------------

def cname_2_name(name: str) -> str:
    return name.replace('-', '_')


def ctype_2_type(t: T.ParamType2, v: t.Any = None) -> T.ParamType3:
    if t == ParamType.ANY:
        return str
    elif t == ParamType.BOOL:
        return bool
    elif t == ParamType.DICT:
        raise ValueError('not implemented')
    elif t == ParamType.FLAG:
        return bool
    elif t == ParamType.LIST:
        raise ValueError('not implemented')
    elif t == ParamType.NONE:
        return type(None)
    elif t == ParamType.NUMBER:
        if v is None or (isinstance(v, str) and v.isdigit()):
            return int
        return float
    elif t == ParamType.TEXT:
        return str


PYTHON_ACCEPTABLE_NUMBER_PATTERN = re.compile(
    r'^ *-?'
    r'(?:[0-9]+'
    r'|[0-9]*\.[0-9]+'
    r'|0b[01]+'
    r'|0x[0-9a-fA-F]+'
    r') *$'
)

SPECIAL_ARGS = {
    ':true' : True,
    ':false': False,
    # ':t': True,
    # ':f': False,
    ':none' : None,
    ':cwd'  : os.getcwd(),
}


def cval_2_val(value: str, type_: ParamType) -> t.Any:
    if value in SPECIAL_ARGS:
        value = SPECIAL_ARGS[value]
    
    # print(':v', arg, type(arg), type, type(type))
    if isinstance(value, str):
        assert type_ in (
            ParamType.TEXT, ParamType.NUMBER, ParamType.ANY
        )
        if type_ == ParamType.TEXT:
            return value
        elif type_ == ParamType.NUMBER:
            assert PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(value)
            return eval(value)
        else:
            if PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(value):
                return eval(value)
            else:
                return value
    elif isinstance(value, bool):
        # warning: bool type is also an "int" type. so
        # `isinstance(True, int)` returns True.
        # to avoid this weird behavior, we must check
        # `isinstance(arg, bool)` before `isinstance(arg, int)`.
        assert type_ in (
            ParamType.FLAG, ParamType.BOOL, ParamType.ANY
        )
    elif isinstance(value, (int, float)):
        assert type_ in (
            ParamType.NUMBER, ParamType.ANY
        )
    elif value is None:
        assert type_ in (
            ParamType.ANY,
        )
    
    return value


def str_2_val(value: str, type_: ParamType) -> t.Any:
    assert type_ not in (ParamType.DICT, ParamType.LIST), (
        'the complex type is not implemented', type_
    )
    if type_ != ParamType.TEXT:
        value = value.strip()
    
    if type_ in (ParamType.ANY, ParamType.NONE):
        if not value:
            return None if type_ == ParamType.NONE else ''
        
        if PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(value):
            out = eval(value)
            assert isinstance(out, (int, float))
            return out
        
        value_lower = value.lower()
        if value_lower in SPECIAL_ARGS:
            return SPECIAL_ARGS[value_lower]
        if value_lower in ('true', 'false'):
            return value_lower == 'true'
        if value_lower in ('none', 'null'):
            return None
        
        return value
    
    if value == ':none':
        return None
    
    if type_ in (ParamType.BOOL, ParamType.FLAG):
        if value.strip().lower() in ('false', ':false', 'f', ':f', '0'):
            return False
        return True
    
    if type_ == ParamType.NUMBER:
        assert PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(value)
        out = eval(value)
        assert isinstance(out, (int, float))
        return out
    
    assert type_ == ParamType.TEXT
    # if ':cwd' in value:  # TODO: use `re` to replace all `:cwd` in `value`
    #     return SPECIAL_ARGS[':cwd']
    # else:
    #     return value
    return value
