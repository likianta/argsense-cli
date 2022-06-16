from argsense import cli


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
