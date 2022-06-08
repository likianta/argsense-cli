import typing as t

__all__ = ['parse_function', 'TParamType']


class T:
    _ParamName = str
    ParamType = t.Literal[
        'any', 'bool', 'dict', 'float', 'int',
        'list', 'none', 'set', 'str', 'tuple',
    ]
    FallbackType = t.Literal['any', 'str']
    _DefaultValue = t.Any
    
    FuncInfo = t.TypedDict('FuncInfo', {
        'name'  : str,
        'args'  : t.List[t.Tuple[_ParamName, ParamType]],
        'kwargs': t.List[t.Tuple[_ParamName, ParamType, _DefaultValue]],
        'return': ParamType,  # noqa
    })


TParamType = T.ParamType


# TODO: fallback_type is not used in current version.
# noinspection PyUnusedLocal
def parse_function(func, fallback_type: T.FallbackType = 'any') -> T.FuncInfo:
    param_count = func.__code__.co_argcount + func.__code__.co_kwonlyargcount
    param_names = func.__code__.co_varnames[:param_count]
    annotations = func.__annotations__
    kw_defaults = func.__defaults__ or ()
    # print(func.__name__, param_count, param_names, annotations, kw_defaults)
    
    func_name = func.__name__
    args: list
    kwargs: list
    return_: str
    
    type_2_str = {
        None : 'none',
        bool : 'bool',
        dict : 'dict',
        float: 'float',
        int  : 'int',
        list : 'list',
        set  : 'set',
        str  : 'str',
        tuple: 'tuple',
    }
    
    args = []
    if kw_defaults:
        arg_names = param_names[:-len(kw_defaults)]
    else:
        arg_names = param_names
    for name in arg_names:
        args.append(
            (name, type_2_str.get(annotations.get(name, str), 'any'))
        )
    
    kwargs = []
    if kw_defaults:
        if isinstance(kw_defaults, tuple):
            kw_defaults = dict(
                zip(param_names[-len(kw_defaults):], kw_defaults)
            )
        for name, value in kw_defaults.items():
            if name in annotations:
                type_ = type_2_str.get(annotations[name], fallback_type)
            else:
                type_ = _deduce_param_type_by_default_value(value)
            kwargs.append((name, type_, value))
    
    result = type_2_str.get(annotations.get('return', None), 'any')
    
    return {
        'name'  : func_name,
        'args'  : args,
        'kwargs': kwargs,
        'return': result,
    }


def _deduce_param_type_by_default_value(default: t.Any) -> T.ParamType:
    dict_ = {
        bool : 'bool',
        dict : 'dict',
        float: 'float',
        int  : 'int',
        list : 'list',
        set  : 'set',
        str  : 'str',
        tuple: 'tuple',
    }
    return dict_.get(type(default), 'any')
