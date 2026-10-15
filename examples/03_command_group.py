from argsense import cli


def install(appid: str):
    """
    Install an app from OSS by querying appid.

    Params:
        appid: The application id.
    """
    print('install', appid)


def upgrade(appid: str):
    """
    Upgrade an installed app to the newest version.

    Params:
        appid: The application id.
    """
    print('upgrade', appid)


def doctor():
    """
    Check the health of the local environment.
    """
    print('all good')


def echo(text: str):
    """
    Print the given text back.

    Params:
        text: The text to echo.
    """
    print(text)


if __name__ == '__main__':
    # groups only change the help interface: the commands are listed as a tree
    # grouped by their group names, while the command line is used exactly the
    # same as `cli.run(...)` -- every command is still invoked by its own name.
    #
    # python examples/03_command_group.py -h
    # python examples/03_command_group.py install my-app
    # python examples/03_command_group.py doctor
    # python examples/03_command_group.py echo hi
    cli.run_group({'app': (install, upgrade), 'debug': (doctor, echo)})

    # the dict form also lets you rename the commands:
    # cli.run_group({
    #     'app': {'install': install, 'upgrade': upgrade},
    #     'debug': {'doctor': doctor, 'echo': echo},
    # })
