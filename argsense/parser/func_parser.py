import typing as t
from inspect import getfullargspec

from .args_parser import ParamType
from .docs_parser import T as T0
from .. import config


class T:
    DocsInfo = T0.DocsInfo
    FallbackType = t.Literal['any', 'str']
    Func = t.Callable
    ParamName = str
    # TODO: shall we use `.args_parser.ParamType` instead?
    PlainParamType = t.Literal[
        'any', 'bool', 'dict', 'flag', 'float', 'int',
        'list', 'none', 'set', 'str', 'tuple',
    ]
    
    ArgsInfo = t.Dict[
        ParamName, t.TypedDict('ArgsInfo', {
            'cname': str,
            'ctype': ParamType,
            'desc' : str,
        })
    ]
    KwArgsInfo = t.Dict[
        ParamName, t.TypedDict('KwargsInfo', {
            'cname'   : str,
            'ctype'   : ParamType,
            'desc'    : str,
            'default' : t.Any,
        })
    ]
    RawInfo = t.TypedDict('RawInfo', {
        'name'  : str,
        'args'  : t.List[t.Tuple[ParamName, PlainParamType]],
        'kwargs': t.List[t.Tuple[ParamName, PlainParamType, t.Any]],
        'return': PlainParamType,  # noqa
    })


class FuncInfo:
    args: T.ArgsInfo
    cname_2_name: t.Dict[str, str]
    desc: str
    kwargs: T.KwArgsInfo
    name: str
    target: t.Callable
    transport_help: bool  # FIXME: temp solution
    
    @classmethod
    def global_kwargs(cls) -> T.KwArgsInfo:
        return {  # noqa
            ':help' : {
                'cname'   : '--help',
                'ctype'   : ParamType.FLAG,
                'desc'    : 'show help message and exit',
                'default' : False,  # False means `not explicitly set by user`.
                #   for example, when user inputs in command line:
                #       `argsense xxx.py -h`  # -> True
                #       `argsense xxx.py`     # -> False
            },
            ':helpx': {
                'cname'   : '--helpx',
                'ctype'   : ParamType.FLAG,
                'desc'    : 'expand all command helps',
                'default' : False,
            },
        }
    
    @classmethod
    def global_cname_2_name(cls) -> t.Dict[str, str]:
        return {
            '--help'  : ':help',
            '--helpx' : ':helpx',
            '-h'      : ':help',
            '-hh'     : ':helpx',
            # DELETE: below are deprecated
            '--:help' : ':help',
            '--:helpx': ':helpx',
            '-:h'     : ':help',
            '-:hh'    : ':helpx',
        }
    
    def __init__(self, info: T.RawInfo):
        from ..converter import name_2_cname
        from ..converter import type_2_ctype
        
        self.name = info['name']
        # self.cname = name_2_cname(self.name, style='cmd')
        self.desc = ''
        # self.return_type = info['return']
        self.args = {}
        self.kwargs = FuncInfo.global_kwargs().copy()
        self.cname_2_name = FuncInfo.global_cname_2_name().copy()
        self.transport_help = False
        
        for name, type in info['args']:
            cname = name_2_cname(name, style='arg')
            self._append_cname(name, cname)
            self._append_cname(name, name_2_cname(name, style='opt'))  # alias
            self.args[name] = {
                'cname': cname,
                'ctype': type_2_ctype(type),
                'desc' : '',
            }
        
        for name, type, default in info['kwargs']:
            cname = name_2_cname(name, style='opt')
            self._append_cname(name, cname)
            self.kwargs[name] = {
                'cname'   : cname,
                'ctype'   : type_2_ctype(type),
                'desc'    : '',
                'default' : default,
            }
    
    @property
    def local_kwargs(self) -> T.KwArgsInfo:
        return {k: v for k, v in self.kwargs.items() if not k.startswith(':')}
    
    def _append_cname(self, name: str, cname: str) -> None:
        assert cname not in self.cname_2_name, (
            f'duplicate cname: `{cname}` (for `{name}`). '
            f'make sure you have not defined `xxx`, `_xxx` and `xxx_` '
            f'(or something like this) in the same function.'
        )
        self.cname_2_name[cname] = name
    
    def fill_docs_info(self, info: T.DocsInfo) -> None:
        self.desc = info['desc']
        for name, value in info['args'].items():
            self.args[name]['desc'] = value['desc']
        for name, value in info['kwargs'].items():
            self.kwargs[name]['desc'] = value['desc']
            if value['cname'] != self.kwargs[name]['cname']:
                # be noted value['cname'] may contain ',', we need to split it.
                for cname in value['cname'].split(','):
                    if cname in self.cname_2_name:
                        continue
                    self.cname_2_name[cname] = name
                    # the `cname` stored in `self.kwargs` is preferred `--xxx`
                    # than `-x`.
                    if cname.startswith('--'):
                        self.kwargs[name]['cname'] = cname


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
    def _normalize_type(self, type_: t.Any) -> T.PlainParamType:
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
    
    def get_arg_type(self, name: str) -> T.PlainParamType:
        if name in self.annotations:
            return self._normalize_type(self.annotations[name])
        else:
            return self._fallback_type
    
    def get_kwarg_type(self, name: str, value: t.Any) -> T.PlainParamType:
        if name in self.annotations:
            t = self._normalize_type(self.annotations[name])
        else:
            t = self.deduce_type_by_value(value)
        if t == 'bool':
            t = 'flag'
        return t
    
    def get_return_type(self) -> T.PlainParamType:
        if 'return' in self.annotations:
            return self._normalize_type(self.annotations['return'])
        else:
            return 'none'
    
    @staticmethod
    def deduce_type_by_value(default: t.Any) -> T.PlainParamType:
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
