"""
The scenes that the README screenshots are recorded from.

Two kinds of scenes live here:

- A console scene is a plain function that plays a shell session: it prints the
  prompt, sets `sys.argv` and calls `cli.run(...)`, exactly the way a user would
  run the script. The recorder swaps in a recording rich console, so whatever a
  scene prints ends up in the image.
- A tui scene is a `TuiScene` value: the commands to list, the optional group
  structure, the terminal size, and an optional coroutine that fills the form
  before the screenshot is taken.

They are driven by `sidework/readme_screenshots.py`.
"""

import sys
import typing as t
from dataclasses import dataclass
from dataclasses import field

from rich.pretty import pretty_repr

# note: the annotations of the demo functions below are deliberately real
# objects, not strings - argsense reads them at runtime to tell the parameter
# types apart, so `from __future__ import annotations` must not be used here.

# ------------------------------------------------------------------------------
# console scenes


CONSOLE_SCENES: t.Dict[str, t.Callable[[], None]] = {}


def console_scene(func: t.Callable[[], None]) -> t.Callable[[], None]:
    """Register a scene under its function name."""
    CONSOLE_SCENES[getattr(func, '__name__')] = func
    return func


def _console() -> t.Any:
    # the recorder replaces this console with a recording one.
    import argsense.renderer.rich.render as R

    return R.console


def _prompt(tokens: str = '', program: str = 'test.py') -> None:
    # a simulated shell prompt, so that a session reads like a real terminal.
    line = '[green]argsense-cli>[/] python {}'.format(program)
    if tokens:
        line += ' ' + tokens
    _console().print(line, highlight=False)


def _run(func: t.Callable, tokens: t.Sequence[str], program: str = 'test.py'):
    sys.argv = [program, *tokens]
    # `cli` is looked up at call time, because the recorder gives every figure
    # a fresh interface (see `readme_screenshots._record_console`).
    from argsense import cli

    return cli.run(func)


@console_scene
def hello() -> None:
    """the "hello world" case of the arg sense chapter."""

    def main(name: str = 'world', *, verbose: bool = False) -> None:
        """
        greet someone.

        params:
            name: who to greet.
            verbose (-v): print more information.
        """
        print('hello {}'.format(name))

    _run(main, ['-h'], program='temp.py')


_LONG_DESC_DOC = """\
install an app.

params:
    appid: the app id (a normalized app name).
    version: the app version to operate on.
        if not given, the last installed version will be used.
    use_exist (-u):
        1. if `version` is not given, will try to use the last installed -
        version.
        2. if `version` is given, but not installed, and if depsland finds
        a newer version already installed, will use the newer one.
            why we do this: due to the design limitation, the cloud drive -
            stores only one "latest" version on the oss side; older -
            versions are discarded as soon as a new version is published. -
            this means user can never retrieve a specific older version at -
            that time. we have to force user to use the newer one.
"""

_LONG_DESC_USE_EXIST = (
    '1. if `version` is not given, will try to use the last installed '
    'version. 2. if `version` is given, but not installed, and if depsland '
    'finds a newer version already installed, will use the newer one. why we '
    'do this: due to the design limitation, the cloud drive stores only one '
    '"latest" version on the oss side; older versions are discarded as soon '
    'as a new version is published. this means user can never retrieve a '
    'specific older version at that time. we have to force user to use the '
    'newer one.'
)


@console_scene
def long_desc_argsense() -> None:
    """how arg sense lays out a long parameter description."""

    def install(appid: str, version: str = '', use_exist: bool = True) -> None:
        pass

    install.__doc__ = _LONG_DESC_DOC
    _run(install, ['-h'], program='long_desc_argsense.py')


@console_scene
def long_desc_argparse() -> None:
    """the same command, written with argparse."""

    import argparse

    parser = argparse.ArgumentParser(
        prog='long_desc_argparse.py', description='install an app.'
    )
    parser.add_argument('appid', help='the app id (a normalized app name).')
    parser.add_argument(
        '--version',
        default='',
        help='the app version to operate on. if not given, the last '
        'installed version will be used.',
    )
    parser.add_argument(
        '-u', '--use-exist', action='store_true', help=_LONG_DESC_USE_EXIST
    )
    parser.print_help()


@console_scene
def long_desc_click() -> None:
    """the same command, written with click."""

    import click

    @click.command()
    @click.argument('appid')
    @click.option(
        '--version',
        default='',
        help='the app version to operate on. if not given, the last '
        'installed version will be used.',
    )
    @click.option('-u', '--use-exist', is_flag=True, help=_LONG_DESC_USE_EXIST)
    def main(appid: str, version: str, use_exist: bool) -> None:
        """install an app."""

    sys.argv = ['long_desc_click.py', '--help']
    main(standalone_mode=False)


@console_scene
def long_desc_typer() -> None:
    """the same command, written with typer."""

    import typer

    def main(
        appid: str,
        version: str = typer.Option(
            '',
            help='the app version to operate on. if not given, the last '
            'installed version will be used.',
        ),
        use_exist: bool = typer.Option(
            False, '--use-exist', '-u', help=_LONG_DESC_USE_EXIST
        ),
    ) -> None:
        """install an app."""

    sys.argv = ['long_desc_typer.py', '--help']
    typer.run(main)


@console_scene
def long_desc_cyclopts() -> None:
    """the same command, written with cyclopts."""

    from cyclopts import App

    app = App(name='long_desc_cyclopts.py', help='install an app.')

    @app.default
    def main(appid: str, version: str = '', *, use_exist: bool = False) -> None:
        """install an app.

        Parameters
        ----------
        appid
            the app id (a normalized app name).
        version
            the app version to operate on. if not given, the last installed
            version will be used.
        use_exist
            1. if `version` is not given, will try to use the last installed
            version. 2. if `version` is given, but not installed, and if
            depsland finds a newer version already installed, will use the
            newer one. why we do this: due to the design limitation, the
            cloud drive stores only one "latest" version on the oss side;
            older versions are discarded as soon as a new version is
            published.
        """

    app(['--help'])


@console_scene
def quick_start() -> None:
    """the "quick start" session."""

    def main(foo: t.Any, bar: t.Any) -> None:
        print('foo={!r}, bar={!r}'.format(foo, bar))

    for tokens in (
        ['-h'],
        ['--help'],
        [':true', ':false'],
        [':empty', ':none'],
        ['123', '456'],
        ['0xFFFF', '0b1111'],
    ):
        _prompt(' '.join(tokens))
        _run(main, tokens)


@console_scene
def param_types() -> None:
    """how the parameter types and special values are shown."""

    def train(
        count: int,
        addr: int,
        rate: float = 0.1,
        tag: str = '',
        verbose: bool = False,
    ) -> None:
        _console().print(pretty_repr(locals()), highlight=False)

    for tokens in (
        ['-h'],
        ['5', '0xFFFF', '0.25', 'abc', ':true'],
        [
            '--count',
            '5',
            '--addr',
            '0xFFFF',
            '--rate',
            '0.25',
            '--tag',
            ':none',
            '--verbose',
        ],
    ):
        _prompt(' '.join(tokens))
        _run(train, tokens)


@console_scene
def varargs_compare() -> None:
    """the comparison of `*args` and `**kwargs` against click."""

    def foo(aaa: int, *bbb, ccc: int = 999, **ddd) -> None:
        _console().print(locals(), highlight=False)

    for tokens in (
        ['-h'],
        ['111', '222', '333', '--ccc', '444', '--ddd', '555', '--eee', ':true'],
    ):
        _prompt(' '.join(tokens))
        _run(foo, tokens)


@console_scene
def docstring_wrap() -> None:
    """how a wrapped description line is rendered."""

    def main(foo, bar) -> None:
        """
        training speak stay try me. nothing generation side trial. seven rate -
        worry not word family.
        lay prepare anything piece method now work interesting. where mission -
        move impact future. daughter remember leave. red read message talk hand.
        similar bed capital public. former east later form people lawyer. -
        operation true similar lose receive compare how film.

        service cold choice model finish. send ask star without huge evening.
        next black there production space treat must often. purpose course -
        actually whatever grow. take perform our billion receive food law.
        result focus property yard let both. baby mind work style.
        """

    _run(main, ['-h'])


@console_scene
def docstring_fields() -> None:
    """how the `params:` fields are rendered."""

    def main(aaa: str, bbb: str = '', ccc: str = '') -> None:
        """
        params:
            aaa: degree serve across recently.
            bbb:
                least support seem success word.
            ccc:
                scientist do war statement pay or reflect. fill -
                get skill scene medical. side generation energy -
                but popular. ago war act nice down.
        """

    _run(main, ['-h'])


@console_scene
def supported_types() -> None:
    """the parameter types that arg sense supports."""

    def main(
        aaa: bool,
        bbb: float,
        ccc: int,
        ddd: str,
        # the README deliberately shows that a `None` default is accepted for
        # a plain (non-optional) annotation, so these are kept as-is.
        eee: bool = None,  # type: ignore
        fff: float = None,  # type: ignore
        ggg: int = None,  # type: ignore
        hhh: str = None,  # type: ignore
        iii: t.Optional[bool] = None,
        jjj: t.Optional[float] = None,
        kkk: t.Optional[int] = 123,
        lll: t.Optional[str] = None,
    ) -> None:
        pass

    _run(main, ['-h'])


@console_scene
def varargs_indepth() -> None:
    """the in-depth session of `*args` and `**kwargs`."""

    def main(aaa, *bbb, ccc=123, **ddd) -> None:
        print(
            'aaa={!r}, bbb={!r}, ccc={!r}, ddd={!r}'.format(aaa, bbb, ccc, ddd)
        )

    for tokens in (
        ['-h'],
        ['mmm', 'nnn', 'ooo', '--ccc', '456', '--ppp', 'qqq'],
    ):
        _prompt(' '.join(tokens))
        _run(main, tokens)


# ------------------------------------------------------------------------------
# tui scenes


@dataclass
class TuiScene:
    """What the recorder needs to take a tui screenshot."""

    commands: t.List[t.Callable]
    groups: t.Optional[t.List[t.Tuple[str, t.List[str]]]] = None
    size: t.Tuple[int, int] = (110, 40)
    prepare: t.Optional[t.Callable[..., t.Any]] = None
    initials: t.Dict[str, t.Dict[str, t.Any]] = field(default_factory=dict)


TUI_SCENES: t.Dict[str, TuiScene] = {}


def tui_scene(func: t.Callable[[], TuiScene]) -> t.Callable[[], TuiScene]:
    """Register a scene builder under its function name."""
    TUI_SCENES[getattr(func, '__name__')] = func()
    return func


@tui_scene
def overview() -> TuiScene:
    """the depsland-like demo: a sidebar of groups and a tab bar."""

    def about() -> None:
        """
        Show basic information about this demo.
        """
        print('depsland-like demo v0.1.0')

    def self_location() -> None:
        """
        Show where this script lives.
        """
        print('C:/apps/depsland')

    def install(
        appid: str, upgrade: bool = True, reinstall: bool = False
    ) -> None:
        """
        Install an app from OSS by querying appid.

        params:
            appid: The application ID (a normalized app name).
            upgrade (-u): Upgrade the app if a newer version is available.
            reinstall (-r): Reinstall the app even if it is already installed.
        """

    def uninstall(appid: str, version: t.Optional[str] = None) -> None:
        """
        Uninstall an application.

        params:
            appid: See `@install:appid`.
            version: The app version to operate on.
                If not given, the last installed version is used.
        """

    def runx(
        appid: str,
        version: str = '',
        use_exist: bool = True,
        *,
        dry_run: bool = False,
    ) -> None:
        """
        Check app exists, if not, download and install it. Then run it.

        params:
            appid: See `@install:appid`.
            version: See `@uninstall:version`.
            use_exist (-u): Reuse the last installed version when possible.
            dry_run: Do not actually launch the app, just print the plan.
        """

    def list_apps(limit: int = 5) -> None:
        """
        List installed apps.

        params:
            limit: How many apps to show at most.
        """

    return TuiScene(
        commands=[install, uninstall, runx, about, list_apps, self_location],
        groups=[
            ('app', ['install', 'uninstall', 'runx']),
            ('info', ['about', 'list-apps', 'self-location']),
        ],
        size=(110, 40),
        initials={'install': {'appid': 'depsland'}},
    )


@tui_scene
def widgets() -> TuiScene:
    """a command with a lot of parameters: every widget kind at once."""

    def configure(
        project_name: str,
        version: str = '0.1.0',
        author: str = '',
        email: str = '',
        description: str = '',
        license: str = 'MIT',
        python_requires: str = '>=3.9',
        homepage: str = '',
        keywords: str = '',
        package_dir: str = '.',
        output_dir: str = 'dist',
        jobs: int = 4,
        timeout: int = 60,
        retries: int = 2,
        build_wheel: bool = True,
        build_sdist: bool = True,
        clean: bool = True,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        """
        A fictional "configure" command with a lot of options.

        params:
            project_name: The project name.
            version: The project version.
            author: The author name.
            email: The author email.
            description: A one line description.
            license: The license identifier, e.g. "MIT".
            python_requires: The supported python versions.
            homepage: The project homepage.
            keywords: A comma separated keyword list.
            package_dir: Where the package lives.
            output_dir: Where the build artifacts go.
            jobs: How many parallel jobs to use.
            timeout: The network timeout, in seconds.
            retries: How many times to retry on failure.
            build_wheel (-w): Build a wheel.
            build_sdist (-s): Build a source distribution.
            clean (-c): Clean the output directory before building.
            verbose (-v): Print more details.
            dry_run (-n): Do not actually build anything.
        """

    return TuiScene(
        commands=[configure],
        size=(110, 40),
        initials={'configure': {'project_name': 'my-project'}},
    )


@tui_scene
def compact() -> TuiScene:
    """a small number input, a triple switch and a switch share one row."""

    def whois_using_port(
        port: int, preview: t.Optional[bool] = None, kill: bool = False
    ) -> None:
        """
        Find out which process is using the given port.

        params:
            port: The port to look up.
            preview: Show what would be done.
                It is a `bool | None`, so the form draws a triple switch for
                it: red for `False`, yellow for `None` and green for `True`.
            kill: Kill the process that holds the port.
        """
        print('port={} preview={} kill={}'.format(port, preview, kill))

    return TuiScene(
        commands=[whois_using_port],
        size=(110, 30),
        initials={'whois_using_port': {'port': '8080'}},
    )


@tui_scene
def log() -> TuiScene:
    """fill the form, run it, and show what the command printed."""

    def main(name: str, age: int) -> None:
        """
        A general types demo.

        params:
            name: Your name.
            age: Your age.
        """
        print('hello {}'.format(name))
        print('you are {} years old'.format(age))

    async def prepare(app: t.Any, pilot: t.Any) -> None:
        from textual.widgets import Input

        app.query_one('#param-main-name', Input).value = 'Alice'
        app.query_one('#param-main-age', Input).value = '18'
        await pilot.pause()
        await pilot.click('#run')

    return TuiScene(commands=[main], size=(110, 34), prepare=prepare)
