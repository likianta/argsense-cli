"""
A simplified, depsland-like demo for the argsense tui.

It mimics the command layout of `depsland/depsland/__main__.py` (many commands,
each with a couple of options), but without any real dependency: every command
just prints what it would do. It is meant to be a playground for the tui.

Usage:
    python test/tui_test/depsland_like.py             # open the tui
    python test/tui_test/depsland_like.py :cli -h     # the plain cli instead
    python test/tui_test/depsland_like.py :itui       # an inline tui

note:
    Because it defaults to `mode='tui'`, pass the `:cli` token to get the
    familiar command line behavior (including `-h`).
"""

import typing as t
from pathlib import Path

from argsense import cli


@cli
def about() -> None:
    """
    Show basic information about this demo.
    """
    print('depsland-like demo v0.1.0')
    print('a playground for the argsense tui')


@cli
def self_location() -> None:
    """
    Show where this script lives.
    """
    print(Path(__file__).resolve())


@cli
def install(appid: str, upgrade: bool = True, reinstall: bool = False) -> None:
    """
    Install an app from OSS by querying appid.

    Args:
        appid: The application ID (a normalized app name).
        upgrade (-u): Upgrade the app if a newer version is available.
        reinstall (-r): Reinstall the app even if it is already installed.
    """
    print(
        'installing {} (upgrade={}, reinstall={})'.format(
            appid, upgrade, reinstall
        )
    )
    for i in range(3):
        print('  step {}/3 done...'.format(i + 1))


@cli
def uninstall(appid: str, version: t.Optional[str] = None) -> None:
    """
    Uninstall an application.

    Args:
        appid: See `@install:appid`.
        version: The app version to operate on.
            If not given, the last installed version is used.
    """
    print('uninstalling {} (version={})'.format(appid, version or '<latest>'))


@cli
def runx(
    appid: str,
    version: str = '',
    use_exist: bool = True,
    *,
    dry_run: bool = False,
) -> None:
    """
    Check app exists, if not, download and install it. Then run it.

    Args:
        appid: See `@install:appid`.
        version: See `@uninstall:version`.
        use_exist (-u): Reuse the last installed version when possible.
        dry_run: Do not actually launch the app, just print the plan.
    """
    print(
        'runx {} {} (use_exist={}, dry_run={})'.format(
            appid, version or '<latest>', use_exist, dry_run
        )
    )


@cli
def list_apps(limit: int = 5) -> None:
    """
    List installed apps.

    Args:
        limit: How many apps to show at most.
    """
    for i in range(min(limit, 5)):
        print('{}. demo-app-{}'.format(i + 1, i + 1))


if __name__ == '__main__':
    cli.run(mode='tui')
