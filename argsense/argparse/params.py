from __future__ import annotations

from enum import Enum
from enum import auto

__all__ = ['ParamType', 'ParamsHolder']


# noinspection PyArgumentList
class ParamType(Enum):
    TEXT = auto()
    NUMBER = auto()
    FLAG = auto()
    BOOL = auto()
    ANY = auto()


class T:
    Args = dict[str, ParamType]
    Kwargs = dict[str, ParamType]
    Param = tuple[str, ParamType]


class ParamsHolder:
    
    def __init__(self, args: T.Args, kwargs: T.Kwargs, **references):
        self._args = [(k, v) for k, v in args.items()]
        self._kwargs = [(k, v) for k, v in kwargs.items()]
        # self._kwargs_subset = [(k, v) for k, v in kwargs.items()
        #                        if not k.startswith(':')]
        self._cnames = references.get('cnames', ('[i]...[/]',))
    
    def get_param(self, name: str = None) -> T.Param:
        if name:
            # let's check kwargs first.
            for i, (k, _) in enumerate(self._kwargs):
                if k == name:
                    return self._kwargs.pop(i)
            for i, (k, _) in enumerate(self._args):
                if k == name:
                    return self._args.pop(i)
            from .exceptions import ParamNotFound
            raise ParamNotFound(name, self._cnames)
        else:
            # check args first.
            if self._args:
                return self._args.pop(0)
            if self._kwargs:
                for i, (k, _) in enumerate(self._kwargs):
                    if not k.startswith(':'):
                        return self._kwargs.pop(i)
            from .exceptions import TooManyArguments
            raise TooManyArguments()
    
    def resolve(self, kwname: str) -> None:
        for i, (k, v) in enumerate(self._kwargs):
            if k == kwname:
                self._kwargs.pop(i)
                break
