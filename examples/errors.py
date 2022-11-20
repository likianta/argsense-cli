"""
screenshots:
    .assets/examples/errors/20221120012143.png
    .assets/examples/errors/20221120012257.png
    .assets/examples/errors/20221120012346.png
"""
import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True, quiet=True)


def test():
    # typo
    yield 'verison'
    yield 'version'
    # misspellings
    yield 'version --add-prefix'
    yield 'version --add-v-prefix'
    
    # insufficient parameters
    yield 'login AAA'
    # wrong type of parameter
    yield 'login AAA BBB CCC'
    # surplus parameters
    yield 'login AAA BBB :true DDD'
    # option form is not correct
    yield 'login AAA BBB --Remember-Me'
    # option ahead of command
    yield 'AAA BBB login'
    yield '--remember-me login AAA BBB'
    
    # wrong type of parameters
    yield 'auto-type-conversion :true bbb ccc'
    yield 'auto-type-conversion 111 :true ccc'


@cli.cmd()
def version(add_v_prefix=False):
    from argsense import __version__
    if add_v_prefix:
        print('v' + __version__)
    else:
        print(__version__)


@cli.cmd()
def login(username: str, password: str, remember_me=False):
    print('login', username, password, remember_me)


@cli.cmd()
def auto_type_conversion(a: int, b: str, c):
    print(a, b, c)


if __name__ == '__main__':
    cli.run()
