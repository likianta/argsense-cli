"""
test the command group feature.

Usage:
    python test/command_group.py -h
    python test/command_group.py install my-app
    python test/command_group.py install my-app --no-upgrade
    python test/command_group.py doctor
    python test/command_group.py :tui      # the tui lists the groups in a sidebar
    python test/command_group.py :itui     # the same, as an inline block

note:
    `cli.run_group(...)` parses the command line exactly like `cli.run(...)`.
    The only difference is the help interface: the cli shows the commands as a
    tree grouped by their group names (see the COMMAND GROUPS panel), and the
    tui lists them in a sidebar.
"""

from argsense import cli


def install(appid: str, upgrade: bool = True) -> None:
    """
    Install an app from OSS by querying appid.

    Params:
        appid: The application id.
        upgrade (-u): Upgrade to the newest version if available.
    """
    print('installing', appid, '(upgrade =', upgrade, ')')


def upgrade(appid: str) -> None:
    """
    Upgrade an installed app to the newest version.

    Params:
        appid: See `@install:appid`.
    """
    print('upgrading', appid)


def run(appid: str, version: str = '') -> None:
    """
    Run an installed app.

    Params:
        appid: See `@install:appid`.
        version: The version to run; empty means the latest one.
    """
    print('running', appid, version or '(latest)')


def doctor() -> None:
    """
    Check the health of the local environment.
    """
    print('all good')


def echo(text: str) -> None:
    """
    Print the given text back.

    Params:
        text: The text to echo.
    """
    print(text)


if __name__ == '__main__':
    cli.run_group({'app': (install, upgrade, run), 'debug': (doctor, echo)})

    # the dict form is supported as well, and lets you rename the commands:
    # cli.run_group(
    #     {
    #         'app': {'install': install, 'upgrade': upgrade, 'run': run},
    #         'debug': {'doctor': doctor, 'echo': echo},
    #     }
    # )
