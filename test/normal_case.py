from argsense import cli


@cli.cmd()
def func_0xa24c(aaa, bbb='', ccc=True):
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    # pox test/normal_case.py -h
    # pox test/normal_case.py func_0xa24c -h
    # pox test/normal_case.py func_0xa24c alpha beta :false
    # pox test/normal_case.py func_0xa24c alpha beta --not-ccc
    cli.run()
