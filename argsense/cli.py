import os
import sys
import typing as t
from textwrap import indent

from . import artist
from .argparse import ParamType
from .console import console
from .parser import parse_docstring
from .parser import parse_function

__all__ = ['cli']


class T:
    # reading order:
    #   follow the tailed marks of code comment: A -> B -> C -> ...
    
    Mode = t.Literal['group', 'command']
    
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
    _FunctionId = int
    _CommandName = str  # name in kebab-case.  # B2
    CommandsDict = t.Dict[  # A1
        _FunctionName, t.TypedDict('CommandsDict', {
            # 'name': _CommandName,  # noqa
            'func': t.Callable,
            'info': CommandInfo,  # noqa
        })
    ]
    
    # WIP proposal
    CommandsDict2 = t.Dict[
        _FunctionId, t.TypedDict('FuncInfo', {
            'func'  : t.Callable,
            'cname' : str,
            'desc'  : str,
            'args'  : t.Dict[
                _ArgName, t.TypedDict('ArgInfo', {
                    'cname': str,
                    'ctype': ParamType,  # noqa
                    'desc' : str,
                })
            ],
            'kwargs': t.Dict[
                _ArgName, t.TypedDict('ArgInfo', {
                    'cname'  : str,
                    'ctype'  : ParamType,  # noqa
                    'desc'   : str,
                    'default': t.Any,
                })
            ],
        })
    ]


class CommandLineInterface:
    """
    TODO: we will add group feature in future version.
    """
    
    def __init__(self):
        self.commands: T.CommandsDict2 = {}
        self._cname_2_func = {}
    
    # -------------------------------------------------------------------------
    # decorators
    
    def cmd(self, name=None) -> t.Callable:
        """
        usage:
            from argsense import cli
            @cli.cmd()
            def foo(...):
                ...
        """
        from .converter import name_2_cname, type_2_ctype
        
        def decorator(func: t.Callable) -> t.Callable:
            nonlocal name
            cmd_name = name or name_2_cname(func.__name__)
            if cmd_name in self._cname_2_func and \
                    (new := func) is not (old := self._cname_2_func[cmd_name]):
                raise Exception(
                    f'duplicate command name: {cmd_name}',
                    f'the recorded function is: {old}',
                    f'the incoming function is: {new}',
                )
            else:
                self._cname_2_func[cmd_name] = func
            
            func_info = parse_function(func)
            docs_info = parse_docstring(func.__doc__ or '')
            
            self.commands[id(func)] = {
                'func'  : func,
                'cname' : name_2_cname(cmd_name),
                'desc'  : docs_info['desc'],
                'args'  : {
                    name: {
                        'cname': name_2_cname(name, style='arg'),
                        'ctype': type_2_ctype(type_),
                        'desc' : docs_info['args'].get(name, ''),
                    } for name, type_ in func_info['args']
                },
                'kwargs': {
                    name: {
                        'cname'  : name_2_cname(name, style='opt'),
                        'ctype'  : type_2_ctype(type_),
                        'desc'   : docs_info['opts'].get(name, ''),
                        'default': value,
                    } for name, type_, value in func_info['kwargs']
                },
            }
            
            return func
        
        return decorator
    
    # -------------------------------------------------------------------------
    # run
    
    def run(self, func=None):
        from . import config
        from .argparse import extract_command_name, parse_argv
        
        console.width = config.CONSOLE_WIDTH
        mode: T.Mode = 'group' if not func else 'command'  # noqa
        
        if func is None:
            if cmd_name := extract_command_name(sys.argv):
                # print(':v', cmd_name)
                func = self._cname_2_func[cmd_name]
        
        result = parse_argv(
            argv=sys.argv,
            mode=mode,
            front_matter={
                'args'  : {} if func is None else {
                    k: v['ctype']
                    for k, v in self.commands[id(func)]['args'].items()
                },
                # FIXME: if func is None, use global options.
                'kwargs': {'help': ParamType.FLAG} if func is None else {
                    'help': ParamType.FLAG, **{
                        k: v['ctype']
                        for k, v in self.commands[id(func)]['kwargs'].items()
                    }
                },
                'index' : {'--help': 'help', '-h': 'help'} if func is None else {
                    '--help': 'help', '-h': 'help', **{
                        n: k
                        for k, v in self.commands[id(func)]['kwargs'].items()
                        for n in v['cname'].split(',')
                    }
                },
            }
        )
        # print(':lv', result)
        if result['command']:
            func = self._cname_2_func[result['command']]
        # FIXME: we take '--help' as the most important option to check. the
        #   '--help' is the only global option for now.
        if result['kwargs'].get('help'):
            self.show(func)
        else:
            self.exec(func, result['args'], result['kwargs'])
    
    def show(self, func):
        """
        reference:
            [lib:click]/core.py : BaseCommand.main()
        """
        if func is None:
            console.print(
                artist.draw_title(
                    prog_name=_detect_program_name(),
                    commands=True,
                    arguments=None,
                    serif_line=False,
                ),
                justify='center'
            )
            
            console.print(
                artist.draw_commands_panel({
                    v['cname']: v['desc']
                    for v in self.commands.values()
                })
            )
        
        else:
            func_info = self.commands[id(func)]
            desc = func_info['desc']
            
            console.print(
                artist.draw_title(
                    prog_name=_detect_program_name(),
                    commands=False,
                    arguments=tuple(
                        v['cname'] for v in func_info['args'].values()
                    ),
                    serif_line=bool(desc),
                ),
                justify='center'
            )
            if desc:
                from rich.text import Text
                rich_desc = Text.from_markup(indent(desc, ' '))
                rich_desc.stylize('grey74')
                console.print(rich_desc)
            
            if args := func_info['args']:
                console.print(
                    artist.draw_arguments_panel({
                        v['cname']: v['desc']
                        for k, v in args.items()
                    })
                )
            
            if kwargs := func_info['kwargs']:
                console.print(
                    artist.draw_options_panel({
                        v['cname']: v['desc']
                        for k, v in kwargs.items()
                    })
                )
        
        # show logo in right-bottom corner.
        # noinspection PyTypeChecker
        console.print(
            artist.post_logo(style='white' if func else 'magenta'),
            justify='right', style='bold', end=' \n'
        )
    
    @staticmethod
    def exec(func: t.Callable, args: t.Sequence, kwargs: dict):
        try:
            func(*args, **kwargs)
        except Exception:
            console.print_exception(show_locals=True)


def _detect_program_name() -> str:
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
        return f'python {name}.py'
    elif (
            os.name == 'nt'
            and main.__package__ == ''
            and not os.path.exists(path)
            and os.path.exists(f'{path}.exe')
    ):
        return f'{name}.exe'
    
    py_module = t.cast(str, main.__package__)
    if name != '__main__':  # a submodule like 'example.cli'
        py_module = f'{py_module}.{name}'.lstrip('.')
    return f'python -m {py_module}'


cli = CommandLineInterface()
