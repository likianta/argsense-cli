"""
screenshots:
    .assets/examples/classic/20220615143658.jpg
    .assets/examples/classic/20220615143730.jpg
    .assets/examples/classic/20220615143751.jpg
    .assets/examples/classic/20220615143817.jpg
"""
from typing import Any

import lk_logger

from argsense import cli

lk_logger.setup(quiet=True, show_varnames=True)


def test():
    """ see `examples/fixture.py : test : docstring` """
    yield '-h'
    yield '-hh'
    yield 'hello-world -h'
    yield 'hello-world'
    yield 'hello-to-someone -h'
    yield 'hello-to-someone Alice'
    yield 'variant-types-1 123 :true cipher'
    yield 'variant-types-1 123 :true cipher --d 1.23'
    yield 'variant-types-2 -h'
    yield 'variant-types-2 1 2 3.12 :true foo :none :false'


@cli.cmd()
def hello_world() -> None:
    """ say hello to the world. """
    print('hello world!')


@cli.cmd()
def greet(name: str, formal=False) -> None:
    """ say hello to the someone.
    
    args:
        name: the name to say hello to.
    
    kwargs:
        formal (-f): if true, say hello formally.
    """
    if formal:
        print(f'hello, {name}!')
    else:
        print(f'hi, {name}!')


@cli.cmd()
def path_includes_whitespace(path: str, *args) -> None:
    print(path, args)


@cli.cmd()
def variant_types_1(a: int, b: bool, c: str, d: float = None):
    """
    argsense supports some basic types more than str.
    (the type-conversion is based on annotations).
    """
    print([(x, type(x)) for x in (a, b, c, d)])


@cli.cmd()
def variant_types_2(a: str, b: int, c: float, d: bool, e, f: 'any', g: Any):
    print([(x, type(x)) for x in (a, b, c, d, e, f, g)], ':l')


if __name__ == '__main__':
    cli.run()
