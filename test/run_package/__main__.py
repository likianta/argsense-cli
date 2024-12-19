from argsense import cli


@cli.cmd()
def func_0xa24c(aaa, bbb='', ccc=''):
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    # pox -m test.run_package -h
    cli.run()
