import os
import sys
import typing as t

from . import artist
from .console import console
from .parser import parse_docstring
from .parser import parse_function

__all__ = ['cli']


class T:
    # reading order:
    #   follow the tailed marks of code comment: A -> B -> C -> ...
    
    _ArgName = str  # C1
    _ArgType = str  # C2
    _DefaultValue = t.Any  # C3
    
    CommandInfo = t.TypedDict('CommandInfo', {  # B2
        'desc'       : str,
        'args'       : t.List[t.Tuple[_ArgName, _ArgType]],
        'args.docs'  : t.Dict[_ArgName, str],
        'kwargs'     : t.List[t.Tuple[_ArgName, _ArgType, _DefaultValue]],
        'kwargs.docs': t.Dict[_ArgName, str],
    })
    
    _FunctionName = str  # name in snake_case.  # B1
    _CommandName = str  # name in kebab-case.  # B2
    CommandsDict = t.Dict[  # A1
        _FunctionName, t.TypedDict('CommandsDict', {
            # 'name': _CommandName,  # noqa
            'func': t.Callable,
            'info': CommandInfo,  # noqa
        })
    ]


class CommandLineInterface:
    """
    TODO: we will add group feature in future version.
    """
    commands: T.CommandsDict = {}
    ''' {
            str command_name: {
                'func': callable,
                'info': dict,
            }, ...
        }
    '''
    
    def add_command(self, name: str, func, info: T.CommandInfo):
        self.commands[name] = {
            'func': func,
            'info': info,
        }
    
    def run(self, func=None):
        """
        reference:
            [lib:click]/core.py : BaseCommand.main()
        """
        # excerpt
        mode = 'group' if not func else 'command'
        args = None if mode == 'group' else tuple(
            x[0].upper()
            for x in self.commands[func.__name__]['info']['args']
        )
        has_args = bool(args)
        # has_args = False if mode == 'group' else bool(
        #     self.commands[func.__name__]['info']['args']
        # )
        
        console.print(
            artist.draw_title(
                prog_name=_detect_program_name(rich=True),
                commands=bool(mode == 'group'),
                arguments=args,
            ),
            justify='center'
        )
        
        if mode == 'group':
            console.print(
                artist.draw_commands_panel({
                    k: v['info']['desc']
                    for k, v in self.commands.items()
                })
            )
        
        if has_args:
            keys = (func.__name__,) if func else self.commands.keys()
            for k in keys:
                v = self.commands[k]['info']
                console.print(
                    artist.draw_arguments_panel({
                        x[0]: v['args.docs'].get(x[0], '')
                        for x in v['args']
                    })
                )
        
        # show logo in right-bottom corner.
        # noinspection PyTypeChecker
        console.print(
            artist.post_logo(style='magenta' if mode == 'group' else 'blue'),
            justify='right', style='bold', end=' \n'
        )
    
    # -------------------------------------------------------------------------
    # decorators
    
    def cmd(self, func):
        func_info = parse_function(func)
        docs_info = parse_docstring(func.__doc__)
        self.add_command(
            func.__name__, func, {
                'desc'       : docs_info['desc'],
                'args'       : func_info['args'],
                'args.docs'  : docs_info['args'],
                'kwargs'     : func_info['kwargs'],
                'kwargs.docs': docs_info['opts'],
            }
        )
        return func


def _detect_program_name(rich=False) -> str:
    """
    determine the program name to be `python ...` or `python -m ...`.
    
    source: ~/click/utils.py : _detect_program_name()
    
    return:
        examples:
            - 'python -m example'
            - 'python example.py'
            - 'example.exe'
    """
    main = sys.modules['__main__']
    path = sys.argv[0]
    name = os.path.splitext(os.path.basename(path))[0]
    
    if getattr(main, '__package__', None) is None:
        if rich:
            return f'python [bright_red]{name}.py[/]'
        else:
            return f'python {name}.py'
    elif (
            os.name == 'nt'
            and main.__package__ == ''
            and not os.path.exists(path)
            and os.path.exists(f'{path}.exe')
    ):
        if rich:
            return f'[bright_red]{name}.exe[/]'
        else:
            return f'{name}.exe'
    
    py_module = t.cast(str, main.__package__)
    if name != '__main__':  # a submodule like 'example.cli'
        py_module = f'{py_module}.{name}'.lstrip('.')
    if rich:
        return f'python -m [bright_red]{py_module}[/]'
    else:
        return f'python -m {py_module}'


cli = CommandLineInterface()
