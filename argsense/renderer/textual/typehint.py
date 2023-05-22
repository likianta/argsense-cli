"""
here are stored shared type hints across multiple modules.
"""
import typing as t

from ...parser.func_parser import FuncInfo


class T:
    FuncInfo = FuncInfo
    # be noticed this should not be an iterator type, because we may use it
    # many times.
    FuncsInfo = t.Union[t.Tuple[FuncInfo, ...], t.List[FuncInfo]]
