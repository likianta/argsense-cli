"""
copied from qmlease.qtcore.binding
"""
import typing as t
from typing import Callable

from .signal import Signal

_grafted = set()


def bind_signal(emitter: t.Union[t.Callable, Signal],
                emit_now=False) -> Callable:
    assert isinstance(emitter, Signal)
    
    def decorator(func):
        uid = (id(emitter), id(func))
        if uid in _grafted:
            return func
        _grafted.add(uid)
        emitter.connect(func)  # noqa
        if emit_now:
            # signal.emit()
            func()  # FIXME: what about args and kwargs?
        return func
    
    return decorator


def connect(a: t.Any, signame: str, func: t.Union[t.Callable, Signal]) -> None:
    if not hasattr(a, signame):
        setattr(a, signame, Signal())
    getattr(a, signame).connect(func)
