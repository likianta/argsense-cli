from argsense import cli


# noinspection PyUnusedLocal
@cli.cmd()
def func0(a_very_very_very_very_very_very_very_very_very_very_long_name: str):
    pass


if __name__ == '__main__':
    cli.run()
