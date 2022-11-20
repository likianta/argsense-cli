import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True)


def test():
    """ see `examples/fixture.py : test : docstring` """
    yield 'test-args-kwargs-1 -h'
    yield 'test-args-kwargs-1 alice'
    yield 'test-args-kwargs-1 --name alice'
    yield 'test-args-kwargs-2 -h'
    yield 'test-args-kwargs-2 alpha 123 456 789 beta gama --not-d holo :true ' \
          ':false :none -e erase -f fuze'


@cli.cmd()
def test_args_kwargs_1(*args, **kwargs):
    print(args, kwargs, ':l')


@cli.cmd()
def test_args_kwargs_2(a, b: int, c=123, *args, d: bool = None, **kwargs):
    print(a, b, c, args, d, kwargs, ':l')


if __name__ == '__main__':
    cli.run()
