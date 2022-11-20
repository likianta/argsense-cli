"""
py examples/advanced.py test-args-kwargs-1 -h
py examples/advanced.py test-args-kwargs-1 alice
py examples/advanced.py test-args-kwargs-1 --name alice
py examples/advanced.py test-args-kwargs-2 -h
py examples/advanced.py test-args-kwargs-2 alpha 123 456 789 beta gama --not-d
    holo :true :false :none -e erase -f fuze
"""
import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True)


@cli.cmd()
def test_args_kwargs_1(*args, **kwargs):
    print(args, kwargs, ':l')


@cli.cmd()
def test_args_kwargs_2(a, b: int, c=123, *args, d: bool = None, **kwargs):
    print(a, b, c, args, d, kwargs, ':l')


if __name__ == '__main__':
    cli.run()
