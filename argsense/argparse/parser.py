from __future__ import annotations

import os
import re
import typing as t
from enum import Enum
from enum import auto

from .argv2 import ArgvVendor

__all__ = ['extract_command_name', 'parse_argv', 'ParamType']


class E:  # Exceptions
    
    class FailedParsingArgv(Exception): ...
    
    class InvalidCommand(Exception): ...


class T:  # Typehint
    _KwArgName = str
    _OptionName = str
    _ParamName = str
    _ParamType = 'ParamType'  # i.e. Enum
    
    ParamsInfo = t.TypedDict('ParamsInfo', {
        'args'  : t.Dict[_ParamName, _ParamType],
        'kwargs': t.Dict[_KwArgName, _ParamType],
        'index' : t.Dict[_OptionName, _KwArgName],
    })
    
    ParsedResult = t.TypedDict('ParsedResult', {
        'command': str,
        'args'   : t.Dict[str, t.Any],
        'kwargs' : t.Dict[str, t.Any],
    })


# noinspection PyArgumentList
class ParamType(Enum):
    TEXT = auto()
    NUMBER = auto()
    FLAG = auto()
    ANY = auto()


def parse_argv(
        argv: list[str],
        mode: t.Literal['group', 'command'],
        front_matter: T.ParamsInfo,
) -> T.ParsedResult:
    # print(argv, front_matter, ':l')
    path, argv = argv[0], argv[1:]
    argv_vendor = ArgvVendor(argv)
    try:
        return _walking_through_argv(argv_vendor, mode, front_matter)
    except:
        argv_vendor.report('TODO')


def _walking_through_argv(
        argv_vendor: ArgvVendor,
        mode: t.Literal['group', 'command'],
        front_matter: T.ParamsInfo
):
    """
    all possible cases (examples):
        python main.py
        python main.py -h
        python main.py --help
        python main.py "'--this-is-a-value'"
        python main.py true
        python main.py "'true'"
    """
    from .context import Context, Token
    ctx = Context()
    
    out = {
        'command': '',
        'args'   : {},  # dict[str name, any value]
        'kwargs' : {},  # dict[str name, any value]
    }
    
    for arg in argv_vendor:
        if ctx.token in (Token.START, Token.READY):
            if arg.startswith('-'):
                if arg.startswith('--'):
                    if arg.startswith('--not-'):
                        option_name = arg.replace('--not-', '--', 1)
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        assert param_type in (ParamType.FLAG, ParamType.ANY)
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        continue
                    else:
                        option_name = arg
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        if param_type == ParamType.FLAG:
                            out['kwargs'][param_name] = True
                            ctx.update(Token.READY)
                            continue
                else:
                    assert arg.count('-') == 1
                    if arg[1:].isupper():
                        option_name = arg.lower()
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        assert param_type in (ParamType.FLAG, ParamType.ANY)
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        continue
                    else:
                        option_name = arg
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        if param_type == ParamType.FLAG:
                            out['kwargs'][param_name] = True
                            ctx.update(ctx.token)
                            continue
                ctx.update(Token.OPTION_NAME)
                ctx.store_param_info(param_name, param_type)
                continue
        
        if ctx.token == Token.START:
            if mode == 'group':
                out['command'] = arg
                ctx.update(Token.READY)
                continue
            else:
                ctx.update(Token.READY)
        
        assert not arg.startswith('-')
        
        if ctx.token == Token.READY:
            param_name: str
            param_type: str
            param_value: t.Union[str, int, float, bool, None]
            
            try:
                param_name = tuple(front_matter['args'])[len(out['args'])]
            except IndexError:
                raise E.FailedParsingArgv('too many arguments', arg,
                                          front_matter, out)
            else:
                param_type = front_matter['args'][param_name]
                param_value = _eval_arg_value(arg, param_type)
            
            out['args'][param_name] = param_value
            ctx.update(Token.READY)
            continue
        
        if ctx.token == Token.OPTION_NAME:
            param_name = ctx.param_name
            param_type = ctx.param_type
            param_value = _eval_arg_value(arg, param_type)
            out['kwargs'][param_name] = param_value
            ctx.update(Token.READY)
            continue


def extract_command_name(argv: list[str]) -> t.Optional[str]:
    option_scope = False
    for arg in argv[1:]:
        if arg.startswith('-'):
            option_scope = True
        elif option_scope:
            option_scope = False
        else:
            return arg
    return None


PYTHON_ACCEPTABLE_NUMBER_PATTERN = re.compile(  # noqa
    r'^-?(?:[0-9]+|[0-9]*\.[0-9]+|0b[01]+|0x[0-9a-fA-F]+)$'
)

SPECIAL_ARGS = {
    ':true' : True,
    ':false': False,
    ':t'    : True,
    ':f'    : False,
    ':none' : None,
    ':cwd'  : os.getcwd(),
}


def _eval_arg_value(arg: str, possible_type) -> t.Any:
    # print(':pv', arg, possible_type)
    
    global PYTHON_ACCEPTABLE_NUMBER_PATTERN, SPECIAL_ARGS
    
    if arg in SPECIAL_ARGS:
        return SPECIAL_ARGS[arg]
    
    if possible_type == ParamType.TEXT:
        return arg
    elif possible_type == ParamType.NUMBER:
        assert PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(arg)
        return eval(arg)
    elif possible_type == ParamType.FLAG:
        assert arg in (':true', ':false')
        return bool(arg == 'true')
    else:
        if PYTHON_ACCEPTABLE_NUMBER_PATTERN.match(arg):
            return eval(arg)
        else:
            return arg