import os
import sys
from textwrap import dedent

from .cli import CommandLineInterface
from .parser import Argv

print(':vl', sys.argv)


def cli() -> None:
    """
    run target module in command line.
    
    params:
        target:
            a ".py" file path, or a directory that contains "__main__.py".
        func:
            function name in target module.
            `*args` and `**kwargs` will be passed to this function.
    """
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == '-h'):
        print(
            '''
            ## Argsense CLI Usage

            ```bash
            {} <target> ...
            ```

            The `<target>` can be a ".py" file path, or a directory that
            contains "__main__.py".
            '''.format(
                'python -m argsense' if sys.argv[0].endswith('__main__.py')
                else os.path.basename(sys.argv[0]).replace('.exe', '')
            ),
            ':r2'
        )
    else:
        assert len(sys.argv) >= 2 and not sys.argv[1].startswith('-')
        _execfile(
            (
                sys.argv[1] if sys.argv[1].endswith('.py') else
                sys.argv[1] + '/__main__.py'  # TODO: not tested
            ),
            *sys.argv[2:]
        )


def tui(*_) -> None:
    """
    run target module in textual interface.
    """
    os.environ['ARGSENSE_UI_MODE'] = 'TUI'
    _run()


def gui(*_) -> None:
    """
    run target module in graphical interface.
    """
    os.environ['ARGSENSE_UI_MODE'] = 'GUI'
    _run()


# _cli = CommandLineInterface('argsense-launcher')
# _cli.add_cmd(cli, name='cli', transfer_help=True)
# _cli.add_cmd(cli, name='run', transfer_help=True)
# _cli.add_cmd(tui, name='tui', transfer_help=True)
# _cli.add_cmd(gui, name='gui', transfer_help=True)


# FIXME or DELETE
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


def _execfile(target: str, *c_args: str) -> None:
    subcli = CommandLineInterface('argsense-subcli')
    
    with open(target, 'r', encoding='utf-8') as f:
        # init subcli commands
        exec(
            '{}\n{}'.format(
                f.read(),
                dedent(
                    '''
                    # print(__name__)
                    # print(__file__)

                    # from types import FunctionType
                    # locals()['__hook__'].update(
                    #     {
                    #         k: v
                    #         for k, v in locals().items()
                    #         if not k.startswith('_')
                    #         and type(v) is FunctionType
                    #     }
                    # )

                    from types import FunctionType
                    public_funcs = tuple(
                        v
                        for k, v in locals().items()
                        if not k.startswith('_')
                        and type(v) is FunctionType
                    )
                    # print(':l', public_funcs)
                    for f in public_funcs:
                        __cli__.add_cmd(f)
                    '''
                )
            ),
            {
                '__name__': '__main__',
                '__file__': os.path.abspath(target),
                '__cli__' : subcli,
            },
            # {
            #     '__cli__': subcli,
            # }
        )
        print(subcli.commands, ':vl')
        
        subcli.exec_argv(
            argv=Argv(
                launcher=('argsense', 'run'),
                target=(target,),
                args=c_args,
            )
        )


if __name__ == '__main__':
    # pox -m argsense -h
    # pox -m argsense <target>
    # por argsense <target>
    # por argsense-cli <target>
    # por argsense-gui <target>
    # por argsense-tui <target>
    
    # _cli.run(transport_help=True)
    
    cli()
