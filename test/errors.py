"""
screenshots:
    .assets/examples/errors/20221120012143.png
    .assets/examples/errors/20221120012257.png
    .assets/examples/errors/20221120012346.png
"""

import shlex
import sys

import lk_logger
from lk_utils import run_cmd_args
from lk_utils.filesniff import relpath

from argsense import cli

lk_logger.setup(quiet=True, show_varnames=True)


@cli.cmd()
def test() -> None:
    this_file = relpath(__file__)
    for args in (
        # typo
        'verison',
        'version',
        # misspellings
        'version --add-prefix',
        'version --add-v-prefix',
        
        # insufficient parameters
        'login AAA',
        # wrong type of parameter
        'login AAA BBB CCC',
        # surplus parameters
        'login AAA BBB :true DDD',
        # option form is not correct
        'login AAA BBB --Remember-Me',
        # option ahead of command
        'AAA BBB login',
        '--remember-me login AAA BBB',
        
        # wrong type of parameters
        'auto-type-conversion :true bbb ccc',
        'auto-type-conversion 111 :true ccc',
    ):
        print(':di')
        run_cmd_args(
            sys.executable, this_file, *shlex.split(args),
            force_term_color=True,
            ignore_error=True,
            verbose=True,
        )


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
    # pox test/errors.py test
    cli.run()
