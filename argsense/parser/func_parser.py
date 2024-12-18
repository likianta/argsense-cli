import typing as t
from inspect import getfullargspec

from enum import Enum, auto

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
            'cname'  : str,
            'ctype'  : ParamType,
            'desc'   : str,
            'default': t.Any,
        })
    ]
    RawInfo = t.TypedDict('RawInfo', {
        'name'  : str,
        'args'  : t.List[t.Tuple[ParamName, PlainParamType]],
        'kwargs': t.List[t.Tuple[ParamName, PlainParamType, t.Any]],
        'return': PlainParamType,  # noqa
    })
    ''' e.g.
        {
            'name': 'run',
            'args': [('appid', 'str'), ('*', 'list')],
            'kwargs': [('_version', 'str', None), ('**', 'dict', {})],
            'return': 'none',
        }
    '''


class ArgumentType(Enum):
    """
    argument type explanation:
        for example here is a function:
            def foo(aaa, *bbb, ccc, ddd=123, **eee):
                pass
        the argument type of each parameter is:
            aaa: required positional argument
            bbb: variable-length positional argument
            ccc: required keyword argument
            ddd: optional keyword argument
            eee: variable-length keyword argument
    """
    REQUIRED_POSITIONAL_ARGUMENT = auto()
    VARIABLE_POSITIONAL_ARGUMENT = auto()
    REQUIRED_KEYWORD_ARGUMENT = auto()
    OPTIONAL_KEYWORD_ARGUMENT = auto()
    VARIABLE_KEYWORD_ARGUMENT = auto()


class FuncInfo:
    args: T.ArgsInfo
    cname_2_name: t.Dict[str, str]
    desc: str
    kwargs: T.KwArgsInfo
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
    GLOBAL_KWARGS: T.KwArgsInfo = {  # noqa
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
    
    # @classmethod
    # def global_kwargs(cls) -> T.KwArgsInfo:
    #     return {  # noqa
    #         ':help' : {
    #             'cname'   : '--help',
    #             'ctype'   : ParamType.FLAG,
    #             'desc'    : 'show help message and exit',
    #             'default' : False,  # False means `not explicitly set by user`.
    #             #   for example, when user inputs in command line:
    #             #       `argsense xxx.py -h`  # -> True
    #             #       `argsense xxx.py`     # -> False
    #         },
    #         ':helpx': {
    #             'cname'   : '--helpx',
    #             'ctype'   : ParamType.FLAG,
    #             'desc'    : 'expand all command helps',
    #             'default' : False,
    #         },
    #     }
    #
    # @classmethod
    # def global_cname_2_name(cls) -> t.Dict[str, str]:
    #     return {
    #         '--help'  : ':help',
    #         '--helpx' : ':helpx',
    #         '-h'      : ':help',
    #         '-hh'     : ':helpx',
    #         # DELETE: below are deprecated
    #         '--:help' : ':help',
    #         '--:helpx': ':helpx',
    #         '-:h'     : ':help',
    #         '-:hh'    : ':helpx',
    #     }
    
    def __init__(self, info: T.RawInfo) -> None:
        # print(info, ':lv')
        from ..converter import name_2_cname
        from ..converter import type_2_ctype
        
        self.name = info['name']
        # self.cname = name_2_cname(self.name, style='cmd')
        self.desc = ''
        # self.return_type = info['return']
        self.args = {}
        self.kwargs = {}
        self.cname_2_name = FuncInfo.GLOBAL_CNAME_2_NAME.copy()
        self.transport_help = False
        
        for name, type in info['args']:
            if name.startswith('*'):
                self.args['*'] = {
                    'cname': name_2_cname(name, style='arg'),
                    'ctype': type_2_ctype(type),
                    'desc' : '',
                }
            else:
                self._register_cname(name_2_cname(name, style='arg'), name)
                self._register_cname(name_2_cname(name, style='opt'), name)
                self.args[name] = {
                    'cname': name_2_cname(name, style='arg'),
                    'ctype': type_2_ctype(type),
                    'desc' : '',
                }
        
        for name, type, default in info['kwargs']:
            if name.startswith('**'):
                self.kwargs['**'] = {
                    'cname'  : name_2_cname(name, style='opt'),
                    'ctype'  : type_2_ctype(type),
                    'desc'   : '',
                    'default': default,
                }
            else:
                self._register_cname(name_2_cname(name, style='opt'), name)
                self.kwargs[name] = {
                    'cname'  : name_2_cname(name, style='opt'),
                    'ctype'  : type_2_ctype(type),
                    'desc'   : '',
                    'default': default,
                }
    
    @property
    def extended_kwargs(self) -> T.KwArgsInfo:
        return {
            **{k: v for k, v in self.kwargs.items()},
            **FuncInfo.GLOBAL_KWARGS
        }
    
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
                self._register_cname(value['cname'], name)
                if value['cshort']:
                    self._register_cname(value['cshort'], name)
                    self.kwargs[name] = {
                        'cname'  : '{}, {}'.format(
                            value['cname'], value['cshort']
                        ),
                        'ctype'  : ParamType.ANY,
                        'desc'   : value['desc'],
                        'default': ...,
                    }
                else:
                    self.kwargs[name] = {
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
        args.append(('*' + spec.varargs, 'any'))
    
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
        kwargs.append(('**' + spec.varkw, 'any', ...))
    
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
