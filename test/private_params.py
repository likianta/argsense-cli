from argsense import cli


@cli.cmd()
def foo(aaa, _bbb, _ccc: bool = True):
    print(aaa, _bbb, _ccc)


if __name__ == '__main__':
    cli.run()
