import shlex
import typing as t

from . import exceptions as e
from .argv import ArgvVendor
from .params import ParamType


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


def parse_argstring(argstring: str) -> t.List[str]:
    return shlex.split(argstring)


def parse_argv(
        argv: t.List[str],
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
    from .params import ParamsHolder
    
    # print(':vl', front_matter)
    
    params = ParamsHolder(
        front_matter['args'], front_matter['kwargs'],
        cnames=tuple(front_matter['index'].keys())
    )
    ctx = Context()
    out = {
        'command': '',
        'args'   : {},  # dict[str name, any value]
        'kwargs' : {},  # dict[str name, any value]
    }
    
    def get_option_name(cname: str) -> str:
        """ convert cname to name. """
        if cname in front_matter['index']:
            return front_matter['index'][cname]
        elif '**' in front_matter['index']:
            return cname.lstrip('-').replace('-', '_')
        else:
            raise e.ParamNotFound(cname, front_matter['index'].keys())
    
    # -------------------------------------------------------------------------
    
    param_name: str
    param_type: ParamType
    param_value: t.Any
    
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
                
                if arg.startswith('--'):
                    try:
                        assert arg == arg.lower()
                    except AssertionError:
                        raise e.MixinCase()
                    
                    if arg.startswith('--not-'):
                        option_name = arg.replace('--not-', '--', 1)
                        param_name = get_option_name(option_name)
                        param_type = params.get_param(param_name)[1]
                        try:
                            assert param_type in (ParamType.FLAG, ParamType.ANY)
                        except AssertionError:
                            raise e.TypeNotCorrect(expected_type='bool')
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        continue
                    else:
                        option_name = arg
                        param_name = get_option_name(option_name)
                        param_type = params.get_param(param_name)[1]
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
                        param_name = get_option_name(option_name)
                        param_type = params.get_param(param_name)[1]
                        try:
                            assert param_type in (ParamType.FLAG, ParamType.ANY)
                        except AssertionError:
                            raise e.TypeNotCorrect(expected_type='bool')
                        out['kwargs'][param_name] = False
                        ctx.update(Token.READY)
                        continue
                    else:
                        option_name = arg
                        param_name = get_option_name(option_name)
                        param_type = params.get_param(param_name)[1]
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
            param_name, param_type = params.get_param()
            param_value = _eval_arg(arg, param_type)
            out['args'][param_name] = param_value
            ctx.update(Token.READY)
            continue
        
        if ctx.token == Token.OPTION_NAME:
            param_name = ctx.param_name
            param_type = ctx.param_type
            param_value = _eval_arg(arg, param_type)
            out['kwargs'][param_name] = param_value
            ctx.update(Token.READY)
            continue
    
    # post check
    if bool(params):
        # if true, there are still arguments not resolved yet.
        if not out['args'] and not out['kwargs']:
            # it means user does not provide any argument to the command.
            # instead of rasing an exception, we guide user to see the help
            # message.
            out['kwargs'][':help'] = True
        elif ':help' not in out['kwargs'] and ':helpx' not in out['kwargs']:
            raise e.InsufficientArguments(
                tuple(front_matter['args'].keys())[len(out['args']):]
            )
    
    return out


def extract_command_name(argv: t.List[str]) -> t.Optional[str]:
    # TODO: need to be improved
    for arg in argv[1:]:
        if arg.startswith('-'):
            continue
        return arg
    return None


def _eval_arg(arg: str, possible_type: ParamType) -> t.Any:
    # print(':pv', arg, possible_type)
    from ...converter import cval_2_val
    try:
        return cval_2_val(arg, possible_type)
    except AssertionError:
        raise e.TypeConversionError(
            expected_type=possible_type.name,
            given_type=str(arg)
        )
