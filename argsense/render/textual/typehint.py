"""
here are stored shared type hints across multiple modules.
"""
import typing as t


class T:
    # noinspection PyTypedDict
    FuncInfo = t.TypedDict('FuncInfo', {
        'func'          : t.Callable,
        'cname'         : str,
        'desc'          : str,
        'args'          : t.Dict[
            str, t.TypedDict('ArgInfo', {
                'cname': str,
                'ctype': str,  # noqa
                'desc' : str,
            })
        ],
        'kwargs'        : t.Dict[
            str, t.TypedDict('ArgInfo', {
                'cname'  : str,
                'ctype'  : str,  # noqa
                'desc'   : str,
                'default': t.Any,
            })
        ],
        'transport_help': bool
    })
    
    FuncsInfo = t.Iterable[FuncInfo]
