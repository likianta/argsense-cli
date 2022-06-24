import lk_logger
lk_logger.setup(quiet=True, show_varnames=True)

from argsense import cli


@cli.cmd()
def anoymous_arguments(username, password='123456'):
    """ input username and password """
    print(username, password)


cli.run()
