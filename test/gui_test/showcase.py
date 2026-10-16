"""
A tour of the gui: the commands below, rendered as a fillable form.

Run it (from the project root) and open the address it prints:

    python test/gui_test/showcase.py

The commands are the ones of `examples/07_tui_showcase.py`, so the two
interfaces can be compared side by side. `:gui` is the only difference from a
normal command line app: drop it (or pass `:cli`) to get the shell prompt
back.

    python test/gui_test/showcase.py :cli build my-project -h

What to look at:

- the left sidebar lists the command groups (`app`, `net`, `debug`);
- the tab bar shows the commands of the group you picked;
- each supported parameter type gets a widget of its own: a text input, a
  number box, a switch, and - for a `bool | None` - a two-mark switch with a
  middle "unset" mark;
- consecutive small widgets (numbers and switches) share a single row -- up
  to four of them, since the window is wide;
- Run calls the command on show, and prints land in the log panel below.
"""

import typing as t

from argsense import cli


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
            it. The middle position says "leave it to the config file", which
            is something the command line cannot spell.
        workers: How many worker processes to spawn.
        backlog: The size of the connection queue.
        keep_alive: How long to hold an idle connection, in seconds.
        daemon: Detach from the terminal and run in the background.
    """
    print(locals())


def fetch(
    url: str,
    # the pep 604 spelling of `Optional[bool]`. Unlike `t.Optional[...]`, it
    # asks for python 3.10+ - below that, use `t.Optional[bool]` instead.
    cache: bool | None = True,  # type: ignore
    timeout: t.Optional[float] = None,
    retries: t.Optional[int] = None,
    token: t.Optional[str] = None,
) -> None:
    """
    Fetch a URL.

    params:
        url: The address to fetch.
        cache: Use the cached response.
            `bool | None` is the pep 604 spelling of `Optional[bool]`, and the
            gui draws both as a three-mark switch. The middle position means
            "decide for me".
        timeout: The network timeout, in seconds.
        retries: How many times to retry on a failure.
        token: The bearer token to send, if any.
    """
    print(locals())


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


if __name__ == '__main__':
    cli.run_group(
        {'app': (build, serve), 'net': (fetch,), 'debug': (doctor, version)},
        mode='gui',
    )
