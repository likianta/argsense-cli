import typing as t
from enum import Enum
from enum import auto

from . import exceptions as e


class ParamType(Enum):
    ANY = auto()
    # BOOL = auto()  # this is totally replaced by `FLAG`.
    DICT = auto()
    FLAG = auto()
    LIST = auto()
    NONE = auto()
    NUMBER = auto()
    TEXT = auto()
    # UNKNOWN = auto()


class T:
    Args = t.Dict[str, ParamType]
    KwArgs = t.Dict[str, ParamType]
    Param = t.Tuple[str, ParamType]


class ParamsHolder:
    
    def __init__(self, args: T.Args, kwargs: T.KwArgs, **references) -> None:
        self._cnames = references.get('cnames', ('[i]...[/]',))
        
        self._args = [(k, v) for k, v in args.items() if k != '*']
        self._kwargs = [(k, v) for k, v in kwargs.items() if k != '**']
        
        self._has_args = '*' in args
        self._has_kwargs = '**' in kwargs
        
    def __bool__(self) -> bool:
        """
        returning True means that there are still parameters to be resolved.
        """
        return bool(self._args)
    
    def get_and_pop_param(self, index: int, name: str = None) -> T.Param:
        if name:
            # let's check kwargs first.
            for i, (k, _) in enumerate(self._kwargs):
                if k == name:
                    return self._kwargs.pop(i)
            for i, (k, _) in enumerate(self._args):
                if k == name:
                    return self._args.pop(i)
            if self._has_kwargs:
                return name, ParamType.ANY
            raise e.ParamNotFound(index, name, self._cnames)
        else:
            # check args first.
            if self._args:
                return self._args.pop(0)
            if self._has_args:
                return self._generate_anonymous_arg_name(), ParamType.ANY
            if self._kwargs:
                for i, (k, _) in enumerate(self._kwargs):
                    if not k.startswith(':'):
                        return self._kwargs.pop(i)
            raise e.TooManyArguments(index)
    
    def resolve(self, kwname: str) -> None:  # note: no usage yet.
        for i, (k, v) in enumerate(self._kwargs):
            if k == kwname:
                self._kwargs.pop(i)
                break
    
    _simple_counter = 0
    
    def _generate_anonymous_arg_name(self) -> str:
        self._simple_counter += 1
        return f'*{self._simple_counter}'
