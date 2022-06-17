from __future__ import annotations

import os
import re
import typing as t
from enum import Enum
from enum import auto

from . import exceptions as e
from .argv import ArgvVendor

__all__ = ['extract_command_name', 'parse_argv', 'ParamType']


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
    # path, argv = argv[0], argv[1:]
    argv_vendor = ArgvVendor(argv)
    try:
        return _walking_through_argv(argv_vendor, mode, front_matter)
    except Exception as err:
        argv_vendor.report(str(err))


def _walking_through_argv(
        argv_vendor: ArgvVendor,
        mode: t.Literal['group', 'command'],
        front_matter: T.ParamsInfo
) -> T.ParsedResult:
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
    
    # shortcuts
    def _get_option_name(cname: str) -> str:
        try:
            return front_matter['index'][cname]
        except KeyError:
            raise e.ParamNotFound(cname, front_matter['index'].keys())

    # -------------------------------------------------------------------------
    
    for arg in argv_vendor:
        # print(':v', arg)
        if ctx.token in (Token.START, Token.READY):
            if arg.startswith('-'):
                if (
                        ctx.token == Token.START
                        and mode == 'group'
                        and out['command'] == ''
                        and front_matter['index'].get(arg)
                        not in (':help', ':helpx')
                ):
                    raise e.ParamAheadOfCommand()
                # else:  # debug
                #     print(':vl', (
                #         ctx.token == Token.START,
                #         mode == 'group',
                #         out['command'] == '',
                #         front_matter['index'].get(arg)
                #     ))
                
                if arg.startswith('--'):
                    try:
                        assert arg == arg.lower()
                    except AssertionError:
                        raise e.MixinCase()
                    
                    if arg.startswith('--not-'):
                        option_name = arg.replace('--not-', '--', 1)
                        param_name = _get_option_name(option_name)
                        param_type = front_matter['kwargs'][param_name]
                        try:
                            assert param_type in (ParamType.FLAG, ParamType.ANY)
                        except AssertionError:
                            raise e.TypeNotCorrect(expected_type='bool')
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        continue
                    else:
                        option_name = arg
                        param_name = _get_option_name(option_name)
                        param_type = front_matter['kwargs'][param_name]
                        if param_type == ParamType.FLAG:
                            out['kwargs'][param_name] = True
                            ctx.update(Token.READY)
                            continue
                else:
                    try:
                        assert arg.count('-') == 1
                    except AssertionError:
                        raise e.ShortOptionFormat(arg)
                    try:
                        assert arg == arg.lower() or arg == arg.upper()
                    except AssertionError:
                        raise e.MixinCase()
                    
                    if arg[1:].isupper():
                        option_name = arg.lower()
                        param_name = _get_option_name(option_name)
                        param_type = front_matter['kwargs'][param_name]
                        try:
                            assert param_type in (ParamType.FLAG, ParamType.ANY)
                        except AssertionError:
                            raise e.TypeNotCorrect(expected_type='bool')
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        continue
                    else:
                        option_name = arg
                        param_name = _get_option_name(option_name)
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
                raise e.TooManyArguments()
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
    
    # post check
    if len(out['args']) < len(front_matter['args']):
        if not out['args'] and not out['kwargs']:
            # cancel check. return [out] as is. (it will be guided to [--help]
            # or [--helpx] by external caller.)
            return out
        if ':help' not in out['kwargs'] and ':helpx' not in out['kwargs']:
            raise e.InsufficientArguments(
                tuple(front_matter['args'].keys())[len(out['args']):]
            )
    # elif len(out['args']) > len(front_matter['args']):
    #     raise e.TooManyArguments()
    
    return out


def extract_command_name(argv: list[str]) -> str | None:
    # TODO: need to be improved
    for arg in argv[1:]:
        if arg.startswith('-'):
            continue
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
