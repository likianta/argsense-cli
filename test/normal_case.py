from argsense import cli


@cli.cmd()
def func_0xa24c(aaa, bbb='', ccc=True):
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    cli.run()
