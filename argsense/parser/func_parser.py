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
    
    ArgsTypeA = t.Dict[
        ParamName, t.TypedDict('ArgsInfo', {
            'cname': str,
            'ctype': ParamType,
            'desc' : str,
        })
    ]
    ArgsTypeB = t.Dict[
        ParamName, t.TypedDict('KwargsInfo', {
            'cname'  : str,
            'ctype'  : ParamType,
            'desc'   : str,
            'default': t.Any,
        })
    ]
    RawInfo = t.TypedDict('RawInfo', {
        'name'  : str,
        'args'  : t.Tuple[
            t.List[t.Tuple[ParamName, PlainParamType]],
            t.List[t.Tuple[ParamName, PlainParamType, t.Any]],
            t.List[t.Tuple[ParamName, PlainParamType]],
            t.List[t.Tuple[ParamName, PlainParamType, t.Any]],
            t.List[t.Tuple[ParamName, PlainParamType]],
        ],
        'return': PlainParamType,  # noqa
    })


# class ArgumentType(Enum):
#     """
#     argument type explanation:
#         for example here is a function:
#             def foo(aaa, *bbb, ccc, ddd=123, **eee):
#                 pass
#         the argument type of each parameter is:
#             aaa: required positional argument
#             bbb: variable-length positional argument
#             ccc: required keyword argument
#             ddd: optional keyword argument
#             eee: variable-length keyword argument
#     """
#     REQUIRED_POSITIONAL_ARGUMENT = auto()
#     VARIABLE_POSITIONAL_ARGUMENT = auto()
#     REQUIRED_KEYWORD_ARGUMENT = auto()
#     OPTIONAL_KEYWORD_ARGUMENT = auto()
#     VARIABLE_KEYWORD_ARGUMENT = auto()


class FuncInfo:
    """
    about args type 0 ~ 4:
        def main(aaa, bbb=..., *ccc, ddd=..., **eee):
            ...
                aaa: type 0
                bbb: type 1
                ccc: type 2
                ddd: type 3
                eee: type 4
    """
    args0: T.ArgsTypeA
    args1: T.ArgsTypeB
    args2: T.ArgsTypeA
    args3: T.ArgsTypeB
    args4: T.ArgsTypeA  # TODO: or `T.ArgsTypeB`?
    cname_2_name: t.Dict[str, str]
    desc: str
    name: str
    target: t.Callable
    transport_help: bool  # FIXME: temp solution
    
    GLOBAL_CNAME_2_NAME: t.Dict[str, str] = {
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
    
    GLOBAL_KWARGS: T.ArgsTypeB = {  # noqa
        ':help' : {
            'cname'  : '--help',
            'ctype'  : ParamType.FLAG,
            'desc'   : 'show help message and exit',
            'default': False,  # False means `not explicitly set by user`.
            #   for example, when user inputs in command line:
            #       `argsense xxx.py -h`  # -> True
            #       `argsense xxx.py`     # -> False
        },
        ':helpx': {
            'cname'  : '--helpx',
            'ctype'  : ParamType.FLAG,
            'desc'   : 'expand all command helps',
            'default': False,
        },
    }
    
    def __init__(self, info: T.RawInfo) -> None:
        # print(info, ':lv')
        from ..converter import name_2_cname
        from ..converter import type_2_ctype
        
        self.name = info['name']
        # self.cname = name_2_cname(self.name, style='cmd')
        self.desc = ''
        # self.return_type = info['return']
        self.cname_2_name = FuncInfo.GLOBAL_CNAME_2_NAME.copy()
        self.transport_help = False
        
        self.args0 = {}
        for name, type in info['args'][0]:
            self._register_cname(name_2_cname(name, style='arg'), name)
            self._register_cname(name_2_cname(name, style='opt'), name)
            self.args0[name] = {
                'cname': name_2_cname(name, style='arg'),
                'ctype': type_2_ctype(type),
                'desc' : '',
            }
        
        self.args1 = {}
        for name, type, default in info['args'][1]:
            self._register_cname(name_2_cname(name, style='opt'), name)
            self.args1[name] = {
                'cname'  : name_2_cname(name, style='opt'),
                'ctype'  : type_2_ctype(type),
                'desc'   : '',
                'default': default,
            }
        
        self.args2 = {}
        if info['args'][2]:
            name, type = info['args'][2][0]
            self.args2['*'] = {
                'cname': name_2_cname(name, style='arg'),
                'ctype': type_2_ctype(type),
                'desc' : '',
            }
        
        self.args3 = {}
        for name, type, default in info['args'][3]:
            self._register_cname(name_2_cname(name, style='opt'), name)
            self.args3[name] = {
                'cname'  : name_2_cname(name, style='opt'),
                'ctype'  : type_2_ctype(type),
                'desc'   : '',
                'default': default,
            }
        
        self.args4 = {}
        if info['args'][4]:
            name, type = info['args'][4][0]
            self.args4['**'] = {
                'cname': name_2_cname(name, style='arg'),
                'ctype': type_2_ctype(type),
                'desc' : '',
            }
    
    @property
    def args(self) -> T.ArgsTypeA:
        return {
            **self.args0,
            **self.args2,
        }
    
    @property
    def kwargs(self) -> T.ArgsTypeB:
        return {
            **self.args1,
            **self.args3,
            **self.args4,
        }
    
    @property
    def extended_kwargs(self) -> T.ArgsTypeB:
        return {
            **self.args1,
            **self.args3,
            **self.args4,
            **FuncInfo.GLOBAL_KWARGS
        }
    
    @property
    def has_var_args(self) -> bool:
        return bool(self.args2)
    
    @property
    def has_var_kwargs(self) -> bool:
        return bool(self.args4)
    
    def fill_docs_info(self, info: T.DocsInfo) -> None:
        self.desc = info['desc']
        
        # FIXME: do not use '<cname>, <cshort>' format. we need a better way.
        
        for name, value in info['args'].items():
            # assert self.args[name]['cname'] == value['cname']
            self.args[name]['desc'] = value['desc']
            if value['cshort']:
                self._register_cname(value['cshort'], name)
                self.args[name]['cname'] = '{}, {}'.format(
                    value['cname'], value['cshort']
                )
            
        for name, value in info['kwargs'].items():
            if name in self.kwargs:
                # assert self.kwargs[name]['cname'] == value['cname']
                self.kwargs[name]['desc'] = value['desc']
                if value['cshort']:
                    self._register_cname(value['cshort'], name)
                    self.kwargs[name]['cname'] = '{}, {}'.format(
                        value['cname'], value['cshort']
                    )
            else:
                assert self.args4
                self._register_cname(value['cname'], name)
                if value['cshort']:
                    self._register_cname(value['cshort'], name)
                    self.args3[name] = {
                        'cname'  : '{}, {}'
                        .format(value['cname'], value['cshort']),
                        'ctype'  : ParamType.ANY,
                        'desc'   : value['desc'],
                        'default': ...,
                    }
                else:
                    self.args3[name] = {
                        'cname'  : value['cname'],
                        'ctype'  : ParamType.ANY,
                        'desc'   : value['desc'],
                        'default': ...,
                    }
    
    def _register_cname(self, cname: str, for_name: str) -> None:
        assert cname not in self.cname_2_name, (
            'duplicate cname: "{}" (for "{}")! make sure you have not defined '
            'parameters like `xxx`, `_xxx` or `xxx_` in the function.'
            .format(cname, for_name)
        )
        self.cname_2_name[cname] = for_name


def parse_function(
    func: T.Func,
    fallback_type: T.FallbackType = 'any'
) -> FuncInfo:
    spec = getfullargspec(func)
    annotations = Annotations(spec.annotations, fallback_type)
    # print(':v', func.__name__, spec.annotations)
    ''' ^
    example:
        def foo(a: str, b: int, c=123, *args, d: bool = False, **kwargs):
            pass
        spec = getfullargspec(foo)
        #   FullArgSpec(
        #       args=['a', 'b', 'c'],
        #       varargs='args',
        #       varkw='kwargs',
        #       defaults=(123,),
        #       kwonlyargs=['d'],
        #       kwonlydefaults={'d': False},
        #       annotations={
        #           'a': <class 'str'>,
        #           'b': <class 'int'>,
        #           'd': <class 'bool'>,
        #       }
        #   )
    '''
    args0 = []
    args1 = []
    args2 = []
    args3 = []
    args4 = []
    
    if spec.defaults:
        args_count = len(spec.args) - len(spec.defaults)
    else:
        args_count = len(spec.args)
    for i in range(0, args_count):
        name = spec.args[i]
        type_ = annotations.get_arg_type(name)
        args0.append((name, type_))
        
    if spec.defaults:
        enum: t.Iterator[t.Tuple[int, int]] = enumerate(
            range(len(spec.args) - len(spec.defaults), len(spec.args))
        )
        for i, j in enum:
            name = spec.args[j]
            default = spec.defaults[i]
            type_ = annotations.get_kwarg_type(name, default)
            args1.append((name, type_, default))
    
    if spec.varargs:
        args2.append(('*' + spec.varargs, 'any'))
    
    if spec.kwonlyargs:
        for name, default in spec.kwonlydefaults.items():
            type_ = annotations.get_kwarg_type(name, default)
            args3.append((name, type_, default))
    
    if spec.varkw:
        args4.append(('**' + spec.varkw, 'any'))
    
    return_ = annotations.get_return_type()
    
    return FuncInfo({
        'name'  : func.__name__,
        'args'  : (args0, args1, args2, args3, args4),
        'return': return_,
    })


class Annotations:
    
    def __init__(
        self,
        annotations: t.Dict[str, t.Any],
        fallback_type: T.FallbackType = 'any'
    ) -> None:
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
        out = str(type_)
        if isinstance(type_, str):
            out = type_
        elif isinstance(type_, t._TypedDictMeta):
            return 'dict'
        elif (
            (x := getattr(type_, '__base__', None)) and
            str(x) == "<class 'tuple'>"
        ):
            return 'tuple'  # typing.NamedTuple
        else:
            # if we are running in lower version python, be noted some classes -
            # are not available.
            _is_legacy_typing: bool = (
                getattr(t, '_LiteralGenericAlias', None) is None
            )
            if _is_legacy_typing:
                if isinstance(type_, t._GenericAlias):
                    return 'any'
            else:
                if isinstance(type_, t._LiteralGenericAlias):
                    # e.g.
                    #   sometype = typing.Literal['A', 'B', 'C']
                    #   type(sometype)  # -> typing._LiteralGenericAlias
                    return 'str'
                elif isinstance(type_, t._UnionGenericAlias):
                    # e.g.
                    #   sometype = typing.Union[str, None]
                    #   type(sometype)  # -> typing._UnionGenericAlias
                    return self._normalize_type(type_.__args__[0])
                elif isinstance(type_, t._GenericAlias):
                    out = type_._name
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
            out = self._normalize_type(self.annotations[name])
        else:
            out = self.deduce_type_by_value(value)
        if out == 'bool':
            out = 'flag'
        # noinspection PyTypeChecker
        return out
    
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
        # noinspection PyTypeChecker
        return dict_.get(type(default), 'any')
