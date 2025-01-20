import os
import sys
from textwrap import dedent

from .cli import CommandLineInterface
from .parser import Argv
from .converter import val_2_cval, name_2_cname

_cli = CommandLineInterface('argsense-launcher')


def cli(target: str, func: str = None, *args, **kwargs) -> None:
    """
    run target module in command line.
    
    params:
        target:
            a ".py" file path, or a directory that contains "__main__.py".
        func:
            function name in target module.
            `*args` and `**kwargs` will be passed to this function.
    """
    if target.endswith('.py'):
        subcli = CommandLineInterface('argsense-subcli')
        
        with open(target, 'r', encoding='utf-8') as f:
            if func:
                assert not func.startswith(('_', '-'))
                func_name = func.replace('-', '_')
                
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
                            public_funcs = (
                                v
                                for k, v in locals().items()
                                if not k.startswith('_')
                                and type(v) is FunctionType
                            )
                            for f in public_funcs:
                                __cli__.add_cmd(f)
                            
                            '''
                        )
                    ),
                    {
                        '__name__': '__main__',
                        '__file__': os.path.abspath(target),
                    },
                    {
                        '__cli__': subcli,
                    }
                )
                print(subcli.commands, ':vl')
                
                cargs = map(val_2_cval, args)
                ckwargs = []
                for k, v in kwargs.items():
                    ckwargs.append(name_2_cname(k, style='opt'))
                    ckwargs.append(val_2_cval(v))
                subcli.exec_argv(
                    argv=Argv.from_sys_argv(
                        (sys.executable, target, func, *cargs, *ckwargs)
                    ),
                    func=func_name,
                )
            else:
                exec(f.read(), {'__name__': '__main__'})
    else:
        raise NotImplementedError


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


_cli.add_cmd(cli, name='cli', transfer_help=True)
_cli.add_cmd(cli, name='run', transfer_help=True)
_cli.add_cmd(tui, name='tui', transfer_help=True)
_cli.add_cmd(gui, name='gui', transfer_help=True)


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
    # py -m argsense -h
    # py -m argsense cli <target.py>
    _cli.run()
