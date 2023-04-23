from __future__ import annotations

import typing as t
from enum import Enum
from enum import auto

__all__ = ['ParamType', 'ParamsHolder']


class ParamType(Enum):
    ANY = auto()
    BOOL = auto()
    DICT = auto()
    FLAG = auto()
    LIST = auto()
    NONE = auto()
    NUMBER = auto()
    TEXT = auto()


class T:
    Args = t.Dict[str, ParamType]
    Kwargs = t.Dict[str, ParamType]
    Param = t.Tuple[str, ParamType]


class ParamsHolder:
    
    def __init__(self, args: T.Args, kwargs: T.Kwargs, **references):
        self._cnames = references.get('cnames', ('[i]...[/]',))
        
        self._args = [(k, v) for k, v in args.items() if k != '*']
        self._kwargs = [(k, v) for k, v in kwargs.items() if k != '**']
        # self._kwargs_subset = [(k, v) for k, v in kwargs.items()
        #                        if not k.startswith(':')]
        
        self._has_args = '*' in args
        self._has_kwargs = '**' in kwargs
        
    def __bool__(self):
        return bool(self._args)
    
    def get_param(self, name: str = None) -> T.Param:
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
            from .exceptions import ParamNotFound
            raise ParamNotFound(name, self._cnames)
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
            from .exceptions import TooManyArguments
            raise TooManyArguments()
    
    def resolve(self, kwname: str) -> None:  # note: no usage yet.
        for i, (k, v) in enumerate(self._kwargs):
            if k == kwname:
                self._kwargs.pop(i)
                break
    
    _simple_counter = 0
    
    def _generate_anonymous_arg_name(self) -> str:
        self._simple_counter += 1
        return f'*{self._simple_counter}'
