import os
import re
import shlex
import typing as t

from . import exceptions as e
from .argv import Argv
from .argv import report
from .params import ParamType
from .params import ParamsHolder


class T:  # Typehint
    _KwArgName = str
    _OptionName = str
    _ParamName = str
    
    ParamsInfo = t.TypedDict('ParamsInfo', {
        'args'  : t.Dict[_ParamName, ParamType],
        'kwargs': t.Dict[_KwArgName, ParamType],
        'index' : t.Dict[_OptionName, _KwArgName],
    })
    
    ParsedResult = t.TypedDict('ParsedResult', {
        'command': str,
        'args'   : t.Dict[_ParamName, t.Any],
        'kwargs' : t.Dict[_ParamName, t.Any],
    })


def parse_argstring(args: str) -> t.List[str]:
    return shlex.split(args)


def parse_argv(
    argv: Argv,
    mode: t.Literal['command', 'group'],
    front_matter: T.ParamsInfo,
) -> t.Optional[T.ParsedResult]:
    try:
        return _walking_through_argv(argv, mode, front_matter)
    except e.ArgvParsingFailed as err:
        if os.getenv('ARGSENSE_DEBUG') == '1':
            raise err
        else:
            report(err.index, str(err))


def _walking_through_argv(
    argv: Argv,
    mode: t.Literal['command', 'group'],
    front_matter: T.ParamsInfo
) -> T.ParsedResult:
    from ...converter import SPECIAL_ARGS, cval_2_val
    
    flag = 'INIT'
    out = {
        'command': '',
        'args'   : {},  # dict[str name, any value]
        'kwargs' : {},  # dict[str name, any value]
    }
    params = ParamsHolder(
        front_matter['args'],
        front_matter['kwargs'],
        cnames=tuple(front_matter['index'].keys())
    )
    temp_store = {}
    
    # -------------------------------------------------------------------------
    
    def feed_anonymous_arg() -> None:
        implicit_name, param_type = params.get_and_pop_param(index)
        param_value = _eval_param_value(arg, param_type)
        out['args'][implicit_name] = param_value
    
    def feed_help() -> None:
        try:
            assert arg in (':h', ':help', '-h', '--help')
        except AssertionError:
            raise e.ParamAheadOfCommand(index)
        out['kwargs'][':help'] = True
    
    def feed_implicit_help() -> None:
        out['kwargs'][':help'] = False  # False means "implicit".
    
    def feed_option_name() -> bool:
        """
        returns: True means "resolved".
        """
        try:
            assert arg == arg.lower()
        except AssertionError:
            raise e.MixinCase(index)
        if arg.startswith(('--not-', '--no-', '--!')):
            option_name = re.sub(r'--(?:not?-|!)', '--', arg, 1)
            param_name = _get_option_name(option_name)
            param_type = params.get_and_pop_param(index, param_name)[1]
            try:
                assert param_type in (ParamType.FLAG, ParamType.ANY)
            except AssertionError:
                raise e.TypeNotCorrect(index, expected_type='bool')
            out['kwargs'][param_name] = False
            return True
        else:
            option_name = arg
            param_name = _get_option_name(option_name)
            param_type = params.get_and_pop_param(index, param_name)[1]
            if param_type == ParamType.FLAG:
                out['kwargs'][param_name] = True
                return True
            else:
                temp_store['param_name'] = param_name
                temp_store['param_type'] = param_type
                return False
    
    def feed_option_value() -> None:
        param_name = temp_store['param_name']
        param_type = temp_store['param_type']
        param_value = _eval_param_value(arg, param_type)
        out['kwargs'][param_name] = param_value
        temp_store.clear()
    
    def feed_possible_func_name() -> None:
        try:
            assert re.match(r'^[a-zA-Z][-\w]*$', arg)
        except AssertionError:
            raise e.ParamAheadOfCommand(index)
        out['command'] = arg.replace('_', '-')
    
    def feed_short_option_name() -> bool:
        try:
            assert arg.count('-') == 1
        except AssertionError:
            raise e.ShortOptionFormat(index, arg)
        try:
            assert arg == arg.lower() or arg == arg.upper()
        except AssertionError:
            raise e.MixinCase(index)
        
        if arg[1:].isupper():
            option_name = arg.lower()
            param_name = _get_option_name(option_name)
            param_type = params.get_and_pop_param(index, param_name)[1]
            try:
                assert param_type in (ParamType.FLAG, ParamType.ANY)
            except AssertionError:
                raise e.TypeNotCorrect(index, expected_type='bool')
            out['kwargs'][param_name] = False
            return True
        else:
            option_name = arg
            param_name = _get_option_name(option_name)
            param_type = params.get_and_pop_param(index, param_name)[1]
            if param_type == ParamType.FLAG:
                out['kwargs'][param_name] = True
                return True
            else:
                temp_store['param_name'] = param_name
                temp_store['param_type'] = param_type
                return False
    
    def feed_special_arg() -> None:
        assert arg in SPECIAL_ARGS
        if arg in (':h', ':help'):
            assert ':help' not in out['kwargs']
            out['kwargs'][':help'] = True
        elif arg == ':loop':
            if mode == 'command' or out['command']:
                out['kwargs'][':loop'] = True
            else:
                raise e.FunctionIsRequired(index)
        else:
            implicit_name, param_type = params.get_and_pop_param(index)
            param_value = SPECIAL_ARGS[arg]
            out['args'][implicit_name] = param_value
    
    # -------------------------------------------------------------------------
    
    def _eval_param_value(x: str, possible_type: ParamType) -> t.Any:
        try:
            return cval_2_val(x, possible_type)
        except AssertionError:
            raise e.TypeConversionError(
                index,
                expected_type=possible_type.name,
                given_type=str(arg)
            )
    
    def _get_option_name(cname: str) -> str:
        """ convert cname to name. """
        if cname in front_matter['index']:
            return front_matter['index'][cname]
        elif '**' in front_matter['kwargs']:
            return cname.lstrip('-').replace('-', '_')
        else:
            raise e.ParamNotFound(index, cname, front_matter['index'].keys())
    
    # -------------------------------------------------------------------------
    
    for index, arg in enumerate(argv.args, argv.argx):
        # print(':v', index, arg)
        if flag == 'INIT':
            if mode == 'group':
                if arg.startswith((':', '-')):
                    feed_help()
                    flag = 'FUNC_NAME'
                else:
                    feed_possible_func_name()
                    flag = 'IDLE'
            else:
                if arg.startswith(':'):
                    feed_special_arg()
                    flag = 'IDLE'
                elif arg.startswith('--'):
                    resolved = feed_option_name()
                    flag = 'IDLE' if resolved else 'OPTION_VALUE'
                elif arg.startswith('-'):
                    resolved = feed_short_option_name()
                    flag = 'IDLE' if resolved else 'OPTION_VALUE'
                else:
                    feed_anonymous_arg()
                    flag = 'IDLE'
        elif flag == 'FUNC_NAME':
            feed_possible_func_name()
            flag = 'WHATEVER'
        elif flag == 'IDLE':
            if arg.startswith(':'):
                feed_special_arg()
            elif arg.startswith('--'):
                resolved = feed_option_name()
                flag = 'IDLE' if resolved else 'OPTION_VALUE'
            elif arg.startswith('-'):
                resolved = feed_short_option_name()
                flag = 'IDLE' if resolved else 'OPTION_VALUE'
            else:
                feed_anonymous_arg()
        elif flag == 'OPTION_VALUE':
            feed_option_value()
            flag = 'IDLE'
        elif flag == 'WHATEVER':
            flag = 'OVER'
            break
    else:
        if flag == 'INIT':
            if bool(params):
                feed_implicit_help()
            flag = 'OVER'
        elif flag in ('FUNC_NAME', 'IDLE'):
            flag = 'OVER'
        elif flag == 'OPTION_VALUE':
            # assume the author had modified "-h" definition and user didn't -
            # know, when user tried to use "-h" in the tail of argv to find -
            # out the help interface, an error would be raised since "-h" -
            # doesn't point to ":help" definition.
            # in this case, we don't want this error happens. instead we -
            # restore "-h" definition to ":help" so that it guides user to the -
            # help interface.
            from ...config import ALLOW_HSHORT_TO_BE_REDEFINED
            try:
                assert (
                    (
                        # 1. assert author had modified "-h" definition.
                        ALLOW_HSHORT_TO_BE_REDEFINED and
                        front_matter['index']['-h'] != ':help'
                    ) and
                    (
                        # 2. user must give "-h" in the end of argv.
                        (
                            mode == 'group' and
                            len(argv.args) == 2 and
                            argv.args[1] == '-h'
                        ) or
                        (
                            mode == 'command' and
                            len(argv.args) == 1 and
                            argv.args[0] == '-h'
                        )
                    )
                )
            except AssertionError:
                raise e.InsufficientArguments(
                    -1, tuple(front_matter['args'].keys())[len(out['args']):]
                )
            # 3. cancel the incoming error, and redirect "-h" to ":help" -
            # definition.
            out['kwargs'][':help'] = True
            flag = 'OVER'
    assert flag == 'OVER', flag
    
    # post check
    if bool(params):
        if ':help' not in out['kwargs']:
            raise e.InsufficientArguments(
                -1, tuple(front_matter['args'].keys())[len(out['args']):]
            )
    return t.cast(T.ParsedResult, out)
