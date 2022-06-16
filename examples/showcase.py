"""
example commands:
    py examples/eg01_showcase.py -h
    py examples/eg01_showcase.py -hh
    py examples/eg01_showcase.py hello-world -h
    py examples/eg01_showcase.py hello-to-someone -h
screenshots:
    .assets/eg01/20220615143658.jpg
    .assets/eg01/20220615143730.jpg
    .assets/eg01/20220615143751.jpg
    .assets/eg01/20220615143817.jpg
"""
import lk_logger

from argsense import cli

lk_logger.setup(show_varnames=True)


@cli.cmd()
def hello_world():
    """ Print 'Hello World!' in the terminal. """
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
