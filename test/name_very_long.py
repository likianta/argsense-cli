from argsense import cli


@cli.cmd()
def a_very_very_very_very_very_very_very_very_very_very_very_very_long_name():
    pass


# noinspection PyUnusedLocal
@cli.cmd()
def func0(a_very_very_very_very_very_very_very_very_very_very_long_name: str):
    pass


# noinspection PyUnusedLocal
@cli.cmd()
def a_very_very_very_very_very_very_very_very_very_very_very_very_long_name_2(
    a_very_very_very_very_very_very_very_very_very_very_long_name: str
):
    pass


if __name__ == '__main__':
    # pox test/name_very_long.py -h
    cli.run()
