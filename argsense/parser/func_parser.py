import typing as t
from inspect import getfullargspec

from .docs_parser import T as T0
from .. import config


class T:
    _DefaultValue = t.Any
    
    DocsInfo = T0.DocsInfo
    FallbackType = t.Literal['any', 'str']
    Func = t.Callable
    ParamName = str
    # TODO: shall we use `.args_parser.ParamType` instead?
    ParamType = t.Literal[
        'any', 'bool', 'dict', 'flag', 'float', 'int',
        'list', 'none', 'set', 'str', 'tuple',
    ]
    
    RawInfo = t.TypedDict('RawInfo', {
        'name'  : str,
        'args'  : t.List[t.Tuple[ParamName, ParamType]],
        'kwargs': t.List[t.Tuple[ParamName, ParamType, _DefaultValue]],
        'return': ParamType,  # noqa
    })


class FuncInfo:
    
    def __init__(self, info: T.RawInfo):
        from ..converter import name_2_cname
        from ..converter import type_2_ctype
        
        self.target = None
        self.name = info['name']
        # self.cname = name_2_cname(self.name, style='cmd')
        self.desc = ''
        self.args = {}
        self.kwargs = {}
        # self.return_type = info['return']
        self.transport_help = False  # FIXME: temp solution
        self._cname_2_name = {}
        
        for name, type in info['args']:
            cname = name_2_cname(name, style='arg')
            self._append_cname(name, cname)
            self.args[name] = {
                'cname': cname,
                'ctype': type_2_ctype(type),
                'desc' : '',
            }
        
        for name, type, default in info['kwargs']:
            cname = name_2_cname(name, style='opt')
            self._append_cname(name, cname)
            self.kwargs[name] = {
                'cname'  : cname,
                'ctype'  : type_2_ctype(type),
                'desc'   : '',
                'default': default,
            }
    
    def _append_cname(self, name: str, cname: str) -> None:
        assert cname not in self._cname_2_name, (
            f'duplicate cname: `{cname}` (for `{name}`). '
            f'make sure you have not defined `xxx`, `_xxx` and `xxx_` '
            f'(or something like this) in the same function.'
        )
        self._cname_2_name[cname] = name
    
    def fill_docs_info(self, info: T.DocsInfo) -> None:
        self.desc = info['desc']
        for name, value in info['args'].items():
            self.args[name]['desc'] = value['desc']
        for name, value in info['kwargs'].items():
            self.kwargs[name]['desc'] = value['desc']
            if value['cname'] != self.kwargs[name]['cname']:
                self._append_cname(name, value['cname'])
                self.kwargs[name]['cname'] = value['cname']
    

def parse_function(
        func: T.Func,
        fallback_type: T.FallbackType = 'any'
) -> FuncInfo:
    spec = getfullargspec(func)
    annotations = Annotations(spec.annotations, fallback_type)
    # print(':v', func.__name__, spec.annotations)
    ''' example:
        def foo(a: str, b: int, c=123, *args, d: bool = False, **kwargs):
            pass
        spec = getfullargspec(foo)
        # -> FullArgSpec(
        #   args=['a', 'b', 'c'],
        #   varargs='args',
        #   varkw='kwargs',
        #   defaults=(123,),
        #   kwonlyargs=['d'],
        #   kwonlydefaults={'d': False},
        #   annotations={
        #       'a': <class 'str'>,
        #       'b': <class 'int'>,
        #       'd': <class 'bool'>,
        #   }
        # )
    '''
    
    args = []
    if spec.defaults:
        args_count = len(spec.args) - len(spec.defaults)
    else:
        args_count = len(spec.args)
    for i in range(0, args_count):
        name = spec.args[i]
        type_ = annotations.get_arg_type(name)
        args.append((name, type_))
    if spec.varargs:
        args.append(('*', 'list'))
    
    kwargs = []
    if spec.defaults:
        enumerator: t.Iterator[t.Tuple[int, int]] = \
            enumerate(range(len(spec.args) - len(spec.defaults),
                            len(spec.args)))
        for i, j in enumerator:
            name = spec.args[j]
            default = spec.defaults[i]
            type_ = annotations.get_kwarg_type(name, default)
            kwargs.append((name, type_, default))
    if spec.kwonlyargs:
        for name, default in spec.kwonlydefaults.items():
            type_ = annotations.get_kwarg_type(name, default)
            kwargs.append((name, type_, default))
    if spec.varkw:
        kwargs.append(('**', 'dict', {}))
    
    return_ = annotations.get_return_type()
    
    return FuncInfo({
        'name'  : func.__name__,
        'args'  : args,
        'kwargs': kwargs,
        'return': return_,
    })


class Annotations:
    
    def __init__(
            self,
            annotations: t.Dict[str, t.Any],
            fallback_type: T.FallbackType = 'any'
    ):
        self.annotations = annotations
        self._fallback_type = fallback_type
        self._type_2_str = {
            'any'    : 'any',
            'anystr' : 'str',
            'bool'   : 'bool',
            'dict'   : 'dict',
            'float'  : 'float',
            'int'    : 'int',
            'list'   : 'list',
            'literal': 'str',
            'none'   : 'none',
            'set'    : 'set',
            'str'    : 'str',
            'tuple'  : 'tuple',
            'union'  : 'any',
        }
        if config.BARE_NONE_MEANS_ANY:
            self._type_2_str['none'] = 'any'
    
    # noinspection PyUnresolvedReferences,PyProtectedMember
    def _normalize_type(self, type_: t.Any) -> T.ParamType:
        if isinstance(type_, t._TypedDictMeta):
            return 'dict'
        elif isinstance(type_, t._LiteralGenericAlias):
            return 'str'
        elif isinstance(type_, t._UnionGenericAlias):
            return self._normalize_type(type_.__args__[0])
        elif isinstance(type_, t._GenericAlias):
            out = type_._name
        elif isinstance(type_, str):
            out = type_
        elif (x := getattr(type_, '__base__', None)) \
                and str(x) == "<class 'tuple'>":
            return 'tuple'  # typing.NamedTuple
        else:
            out = str(type_)
        
        assert isinstance(out, str)
        out = out.lower()
        if out.startswith('<class '):
            out = out[8:-2]  # "<class 'list'>" -> "list"
        if '[' in out:
            out = out.split('[', 1)[0]
        
        # print(':v', type_, out)
        if out in self._type_2_str:
            return self._type_2_str[out]
        return 'any'
    
    def get_arg_type(self, name: str) -> T.ParamType:
        if name in self.annotations:
            return self._normalize_type(self.annotations[name])
        else:
            return self._fallback_type
    
    def get_kwarg_type(self, name: str, value: t.Any) -> T.ParamType:
        if name in self.annotations:
            t = self._normalize_type(self.annotations[name])
        else:
            t = self.deduce_type_by_value(value)
        if t == 'bool':
            t = 'flag'
        return t
    
    def get_return_type(self) -> T.ParamType:
        if 'return' in self.annotations:
            return self._normalize_type(self.annotations['return'])
        else:
            return 'none'
    
    @staticmethod
    def deduce_type_by_value(default: t.Any) -> T.ParamType:
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
