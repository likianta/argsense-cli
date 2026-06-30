"""
screenshots:
    .assets/examples/errors/20221120012143.png
    .assets/examples/errors/20221120012257.png
    .assets/examples/errors/20221120012346.png
"""

import shlex
import sys

from lk_utils import run_cmd_args
from neoprint import print

from argsense import cli


@cli
def test() -> None:
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
        print(':di', args)
        run_cmd_args(
            sys.executable, __file__, *shlex.split(args),
            force_term_color=True,
            ignore_error=True,
            verbose=True,
        )


@cli
def version(add_v_prefix=False):
    from argsense import __version__
    if add_v_prefix:
        print('v' + __version__)
    else:
        print(__version__)


@cli
def login(username: str, password: str, remember_me=False):
    print('login', username, password, remember_me)


@cli
def auto_type_conversion(a: int, b: str, c):
    print(a, b, c)


if __name__ == '__main__':
    # python test/error_checking.py test
    cli.run()
