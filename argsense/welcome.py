"""
The demo behind `python -m argsense welcome`.

It lives inside the package (rather than in `examples/`) so that an installed
argsense can show it without the repository at hand. The commands are the
ones `examples/07_tui_showcase.py` and `examples/08_gui_showcase.py` use, so
the three interfaces can be compared side by side.
"""

import typing as t

from .cli import cli


def build(
    project: str,
    version: str = '0.1.0',
    jobs: int = 4,
    retries: int = 2,
    rate: float = 1.0,
    timeout: float = 60.0,
    wheel: bool = True,
    sdist: bool = False,
    clean: bool = False,
    verbose: bool = False,
) -> None:
    """
    Build a project.

    params:
        project: The project name.
        version: The version to stamp on the artifacts.
        jobs: How many steps to run in parallel.
        retries: How many times to retry a failed step.
        rate: The compression level, from 0.0 to 9.0.
        timeout: The per step timeout, in seconds.
        wheel: Build a wheel.
        sdist: Build a source distribution.
        clean: Empty the output directory first.
        verbose (-v): Print every command that is run.
    """
    print(locals())


def serve(
    port: int,
    host: str = '127.0.0.1',
    reload: t.Optional[bool] = None,
    workers: int = 1,
    backlog: int = 128,
    keep_alive: float = 5.0,
    daemon: bool = False,
) -> None:
    """
    Start the development server.

    params:
        port: The port to listen on.
        host: The interface to bind to.
        reload: Restart when a source file changes.
            It is a `bool | None`, so the form draws a three-mark switch for
            it. The middle position says "leave it to the config file".
        workers: How many worker processes to spawn.
        backlog: The size of the connection queue.
        keep_alive: How long to hold an idle connection, in seconds.
        daemon: Detach from the terminal and run in the background.
    """
    print(locals())


def fetch(
    url: str,
    cache: bool | None = True,  # type: ignore
    timeout: t.Optional[float] = None,
    retries: t.Optional[int] = None,
    token: t.Optional[str] = None,
) -> str:
    """
    Fetch a URL.

    params:
        url: The address to fetch.
        cache: Use the cached response.
            `bool | None` is drawn as a three-mark switch, the same as
            `Optional[bool]`. The middle position means "decide for me".
        timeout: The network timeout, in seconds.
        retries: How many times to retry on a failure.
        token: The bearer token to send, if any.

    It returns a status string, which is what the log panel shows after the
    command's own prints (`: done -> 'ok'`).
    """
    print(locals())
    return 'ok'


def doctor(verbose: bool = False) -> None:
    """
    Check the local environment.

    params:
        verbose (-v): Show every check that was made.
    """
    print('python ... ok')
    print('network  ... ok')


def version() -> None:
    """Show the version of this demo."""
    print('demo v0.1.0')


def run(
    mode: t.Literal['cli', 'tui', 'gui'] = 'gui', *, window: bool = True
) -> None:
    """Open the showcase in the given interface."""
    kwargs = {'window': window} if mode == 'gui' else {}
    cli.run_group(
        {'app': (build, serve), 'net': (fetch,), 'debug': (doctor, version)},
        mode=mode,
        **kwargs,
    )


if __name__ == '__main__':
    run('gui')
