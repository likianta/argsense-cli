"""
example commands:
    py examples/eg01_showcase.py -h
    py examples/eg01_showcase.py -hh
    py examples/eg01_showcase.py hello-world -h
    py examples/eg01_showcase.py hello-to-someone -h
screenshots:
    .assets/20220615125340.jpg
    .assets/20220615125501.jpg
    .assets/20220615125505.jpg
"""
from argsense import cli


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
