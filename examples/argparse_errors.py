import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True, quiet=True)


@cli.cmd()
def version(add_v_prefix=False):
    """
    test cases:
        typo on command name:
            python3 argparse_errors.py verison
                                       ~~~~~~~
        typo on option name:
            python3 argparse_errors.py version --add-prefix
                                               ~~~~~~~~~~~~
    """
    from argsense import __version__
    if add_v_prefix:
        print('v' + __version__)
    else:
        print(__version__)


@cli.cmd()
def login(username: str, password: str, remember_me=False):
    """
    test cases:
        insufficient parameters:
            python3 argparse_errors.py login AAA
        surplus parameters:
            python3 argparse_errors.py login AAA BBB :true
        wrong type of parameter:
            python3 argparse_errors.py login AAA BBB --remember-me CCC
        option form is not correct:
            python3 argparse_errors.py login AAA BBB --Remember-Me
        option ahead of command:
            python3 argparse_errors.py AAA BBB login
            python3 argparse_errors.py --remember-me login AAA BBB
    """
    print('login', username, password, remember_me)


cli.run()
