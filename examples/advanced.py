"""
py examples/advanced.py test-args-kwargs -h
py examples/advanced.py test-args-kwargs alpha 123 456 789 beta gama --not-d
    holo :true :false :none -e erase -f fuze
"""
import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True)


@cli.cmd()
def test_args_kwargs(a, b: int, c=123, *args, d: bool = None, **kwargs):
    print(a, b, c, args, d, kwargs, ':l')


if __name__ == '__main__':
    cli.run()
