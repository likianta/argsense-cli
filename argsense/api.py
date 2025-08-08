import shlex
import typing as t
from types import FunctionType
from . import config
from . import parser as p


def run_func(
    func: FunctionType,
    argstring: str,
    launcher: str = 'python',
    target: str = '<target>',
) -> t.Any:
    """
    limitation:
        - cannot use ":help" in argstring.
        - cannot use ":loop" in argstring.
    """
    func_info = p.parse_function(func, fallback_type=config.FALLBACK_TYPE)
    docs_info = p.parse_docstring(func.__doc__ or '', func_info)
    func_info.fill_docs_info(docs_info)
    
    result = p.parse_argv(
        p.Argv(launcher, target, shlex.split(argstring)),
        mode='command',
        front_matter={
            'args'  : {
                k: v['ctype']
                for k, v in (
                    {} if func_info is None else
                    func_info.args
                ).items()
            },
            'kwargs': {
                k: v['ctype']
                for k, v in (
                    p.FuncInfo.GLOBAL_KWARGS if func_info is None else
                    func_info.extended_kwargs
                ).items()
            },
            'index' : (
                p.FuncInfo.GLOBAL_CNAME_2_NAME if func_info is None else
                func_info.cname_2_name
            )
        }
    )
    assert ':help' not in result['kwargs']
    assert ':loop' not in result['kwargs']
    
    _args, _kwargs = result['args'].values(), result['kwargs']
    return func(*_args, **_kwargs)
