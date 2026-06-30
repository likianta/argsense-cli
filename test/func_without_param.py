import sys

from lk_utils import run_cmd_args
from neoprint import print

from argsense import cli


@cli
def main() -> None:
    def run(*args) -> None:
        print(':dp', args)
        run_cmd_args(
            sys.executable, __file__, *args, verbose=True, force_term_color=True
        )

    # run()
    run('-h')
    run('case1')
    run('case1', '-h')
    run('case2')
    run('case2', '-h')


@cli
def case1() -> None:
    print('hello world')


@cli
def case2() -> None:
    """
    no param, but has desc.
    """
    print('hello world')


if __name__ == '__main__':
    # python test/func_without_param.py main
    cli.run()
