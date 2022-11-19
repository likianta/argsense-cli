"""
example commands:
    py examples/classic.py -h
    py examples/classic.py -hh
    py examples/classic.py hello-world -h
    py examples/classic.py hello-to-someone -h
screenshots:
    .assets/examples/classic/20220615143658.jpg
    .assets/examples/classic/20220615143730.jpg
    .assets/examples/classic/20220615143751.jpg
    .assets/examples/classic/20220615143817.jpg
"""
import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True, quiet=True)


@cli.cmd()
def hello_world():
    print('Hello World!')


@cli.cmd()
def hello_to_someone(name: str, title_case=True):
    """ Say hello to the given name.
    
    args:
        name: The name to say hello to.
    
    kwargs:
        title_case (-t): Force using title case.
            For example, if the name is "john", it will be "John"; if the name -
            is "john smith", it will be "John Smith".
    """
    if title_case:
        name = name.title()
    print(f'Hello {name}!')


cli.run()
