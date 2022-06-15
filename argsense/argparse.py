from __future__ import annotations

import os
import re
import sys
import typing as t
from enum import Enum
from enum import auto

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
        'prog_head': str,
        'command'  : str,
        'args'     : t.Dict[str, t.Any],
        'kwargs'   : t.Dict[str, t.Any],
    })


# noinspection PyArgumentList
class ParamType(Enum):
    TEXT = auto()
    NUMBER = auto()
    FLAG = auto()
    ANY = auto()


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
    param_type: str
    
    last_last_arg: str = None
    last_arg: str = None
    arg: str = None
    
    def __init__(self):
        self.token = Token.START
    
    def update(self, token: Token):
        self.last_last_token = self.last_token
        self.last_token = self.token
        self.token = token
    
    def store_param_info(self, name: str, type_: str):
        self.param_name = name
        self.param_type = type_


def parse_argv(
        argv: list[str],
        mode: t.Literal['group', 'command'],
        front_matter: T.ParamsInfo,
) -> T.ParsedResult:
    # print(argv, front_matter, ':l')
    path, argv = argv[0], argv[1:]
    out = {
        'prog_head': _get_program_head(path),
        'command'  : '',
        'args'     : {},  # dict[str name, any value]
        'kwargs'   : {},  # dict[str name, any value]
    }
    
    ctx = Context()
    
    def walking_through_argv(argv: list[str]):
        if argv:
            arg = argv.pop(0)
        else:
            return
        
        """
        all possible cases (examples):
            python main.py
            python main.py -h
            python main.py --help
            python main.py "'--this-is-a-value'"
            python main.py true
            python main.py "'true'"
        """
        
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
                        return walking_through_argv(argv)
                    else:
                        option_name = arg
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        if param_type == ParamType.FLAG:
                            out['kwargs'][param_name] = True
                            ctx.update(Token.READY)
                            return walking_through_argv(argv)
                else:
                    assert arg.count('-') == 1
                    if arg[1:].isupper():
                        option_name = arg.lower()
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        assert param_type in (ParamType.FLAG, ParamType.ANY)
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        return walking_through_argv(argv)
                    else:
                        option_name = arg
                        param_name = front_matter['index'][option_name]
                        param_type = front_matter['kwargs'][param_name]
                        if param_type == ParamType.FLAG:
                            out['kwargs'][param_name] = True
                            ctx.update(ctx.token)
                            return walking_through_argv(argv)
                ctx.update(Token.OPTION_NAME)
                ctx.store_param_info(param_name, param_type)
                return walking_through_argv(argv)
        
        if ctx.token == Token.START:
            if mode == 'group':
                out['command'] = arg
                ctx.update(Token.READY)
                return walking_through_argv(argv)
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
            return walking_through_argv(argv)
        
        if ctx.token == Token.OPTION_NAME:
            param_name = ctx.param_name
            param_type = ctx.param_type
            param_value = _eval_arg_value(arg, param_type)
            out['kwargs'][param_name] = param_value
            ctx.update(Token.READY)
            return walking_through_argv(argv)
    
    walking_through_argv(argv)
    
    return out


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


def _get_program_head(path: str) -> str:
    """
    determine the program name to be `python ...` or `python -m ...`.

    source: `lib:click/utils.py : _detect_program_name()`
    
    args:
        path: comes from `sys.argv[0]`.
    
    return:
        examples:
            - 'python -m example'
            - 'python example.py'
            - 'example.exe'  # for windows only
    """
    main = sys.modules['__main__']
    name = os.path.splitext(os.path.basename(path))[0]
    #   file name without extension
    
    if getattr(main, '__package__', None) is None:
        return f'python {name}.py'
    elif (
            os.name == 'nt'
            and main.__package__ == ''
            and not os.path.exists(path)
            and os.path.exists(f'{path}.exe')
    ):
        return f'{name}.exe'
    
    py_module = t.cast(str, main.__package__)
    if name != '__main__':  # a submodule like 'example.cli'
        py_module = f'{py_module}.{name}'.lstrip('.')
    return f'python -m {py_module}'


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
