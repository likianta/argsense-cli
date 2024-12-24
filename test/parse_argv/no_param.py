from argsense import cli


@cli.cmd()
def case1() -> None:
    print('hello world')


@cli.cmd()
def case2() -> None:
    """
    no param, but has desc.
    """
    print('hello world')


if __name__ == '__main__':
    # pox test/parse_argv/no_param.py -h
    # pox test/parse_argv/no_param.py case1 -h
    # pox test/parse_argv/no_param.py case2 -h
    cli.run()
