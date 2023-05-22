import os
import sys
from textwrap import dedent

from rich import print as rprint
from rich.markdown import Markdown

from .cli import CommandLineInterface

_cli = CommandLineInterface('argsense-launcher')


@_cli.cmd()
def help() -> None:
    """
    show full instructions about using argsense cli.
    :point_right: [magenta]`py -m argsense help`[/]
    """
    rprint(Markdown(dedent('''
        # Argsense Help
        
        ## Usage
        
        Run argsense in CLI mode:
        
        ```shell
        py -m argsense cli hello.py ...
        ```
        
        Run argsense in GUI mode:
        
        ```shell
        py -m argsense gui hello.py ...
        ```
        
        Run argsense in TUI mode:
        
        ```shell
        py -m argsense tui hello.py ...
        ```
        
        We've also provided a shortcut for GUI & TUI mode:
        
        ```shell
        argsense-gui hello.py ...
        argsense-tui hello.py ...
        ```
        
        But in more general cases, you can simply use `python3` to start your
        target script:
        
        ```shell
        python3 hello.py ...
        ```
        
        The mode of argsense depends on what the script author has defined:
        
        ```python
        # hello.py
        ...
        if __name__ == '__main__':
            cli.run_tui()   # force run in TUI mode
            cli.run_cli()   # force run in CLI mode
            cli.run()       # auto detect mode
        ```
        
        For auto detection, it depends on what user's command is:
        
        ```shell
        # the only way to run in TUI mode
        python3 hello.py
        
        # otherwise, always run in CLI mode
        python3 hello.py -h
        python3 hello.py --name abc
        python3 hello.py --name abc -h
        python3 hello.py ...
        ```
        
        ## Practical Suggestions
        
        Run argsense in CLI mode:
        
        ```shell
        python3 hello.py ...
        ```
        
        Run argsense in TUI mode:
        
        ```shell
        argsense hello.py ...
        ```
    ''')))


@_cli.cmd()
def cli(*_) -> None:
    """
    run argsense in CLI mode.
    :point_right: [magenta]`py -m argsense cli [yellow i]target[/] -
    [default dim i]params[/]`[/]
    """
    os.environ['ARGSENSE_UI_MODE'] = 'CLI'
    _run()


@_cli.cmd()
def gui(*_) -> None:
    """
    run argsense in GUI mode.
    :point_right: [magenta]`py -m argsense gui [yellow dim i]target[/]`[/]
    """
    os.environ['ARGSENSE_UI_MODE'] = 'GUI'
    _run()


@_cli.cmd()
def tui(*_) -> None:
    """
    run argsense in TUI mode.
    :point_right: [magenta]`py -m argsense tui [yellow i]target[/]`[/]
    """
    os.environ['ARGSENSE_UI_MODE'] = 'TUI'
    _run()


def _run() -> None:
    # print(sys.argv, ':vf2')
    #   e.g. ['<argsense>/__main__.py', 'tui', ...]
    sys.argv.pop(0)
    sys.argv.pop(0)
    # print(':f2sl', loads(sys.argv[0], 'plain'))
    with open(sys.argv[0], 'r') as f:
        code = f.read()
    exec(code, {
        '__name__': '__main__',
        '__file__': os.path.abspath(sys.argv[0]),
    })


if __name__ == '__main__':
    # py -m argsense help
    # py -m argsense cli <target.py>
    # py -m argsense tui <target.py>
    # argsense <target.py>
    _cli.run_cli()
