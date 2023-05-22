import typing as t

_exec: t.Optional[t.Callable] = None


def add_post_exec(func: t.Callable) -> None:
    global _exec
    _exec = func


def post_exec() -> t.Any:
    return _exec and _exec()
