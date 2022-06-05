import os
import sys
import typing as t
from textwrap import indent

from . import artist
from .argparse import ParamType
from .console import console
from .name_converter import name_2_cname
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
            'func': t.Callable,
            'cname': str,
            'args': t.Dict[
                _ArgName, t.TypedDict('ArgInfo', {
                    'cname': str,
                    'ctype': ParamType,  # noqa
                    'desc': str,
                })
            ],
            'kwargs': t.Dict[
                _ArgName, t.TypedDict('ArgInfo', {
                    'cname': str,
                    'ctype': ParamType,  # noqa
                    'desc': str,
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
        from .parser.func_parser import TParamType as ParamType1
        from .argparse import ParamType as ParamType2

        def type_2_ctype(t: ParamType1) -> ParamType2:
            return {
                'str'  : ParamType2.TEXT,
                'int'  : ParamType2.NUMBER,
                'float': ParamType2.NUMBER,
                'bool' : ParamType2.FLAG,
                # 'list' : ParamType2.LIST,
                # 'tuple': ParamType2.LIST,
                # 'set'  : ParamType2.LIST,
                # 'dict' : ParamType2.DICT,
                'any'  : ParamType2.ANY,
                # 'none': ParamType2.NONE,
            }.get(t, ParamType2.ANY)

        def decorator(func: t.Callable) -> t.Callable:
            nonlocal name, type_2_ctype
            cmd_name = name or func.__name__
            if cmd_name in self._cname_2_func and \
                    (new := func) is not (old := self._cname_2_func[cmd_name]):
                raise Exception(
                    f'duplicate command name: {cmd_name}',
                    f'the recorded function is: {old}',
                    f'the incoming function is: {new}',
                )
            
            func_info = parse_function(func)
            docs_info = parse_docstring(func.__doc__)
            
            self.commands[id(func)] = {
                'func': func,
                'cname': name_2_cname(cmd_name),
                'args': {
                    name: {
                        'cname': name_2_cname(name),
                        'ctype': type_2_ctype(type_),
                        'desc': docs_info['args'].get(name, ''),
                    } for name, type_ in func_info['args']
                },
                'kwargs': {
                    name: {
                        'cname': name_2_cname(name, is_option=True),
                        'ctype': type_2_ctype(type_),
                        'desc': docs_info['args'].get(name, ''),
                        'default': value,
                    } for name, type_, value in func_info['kwargs']
                },
            }
        
            return func
        return decorator
    
    # -------------------------------------------------------------------------
    # run
    
    def run(self, func=None):
        from .argparse import parse_argv
        result = parse_argv(
            argv=sys.argv,
            mode='group' if not func else 'command',  # noqa
            front_matter={
                'args': {} if func is None else {
                    k: v['ctype']
                    for k, v in self.commands[id(func)]['args'].items()
                },
                # FIXME: if func is None, use global options.
                'kwargs': {
                    k: v['ctype']
                    for k, v in self.commands[id(func)]['kwargs'].items()
                },
                'index': {
                    n: k
                    for k, v in self.commands[id(func)]['kwargs'].items()
                    for n in v['cname'].split(';')
                },
            }
        )
        print(':lv', result)
        self.show(func)
        self.exec(func, sys.argv[1:])
    
    def show(self, func=None):
        """
        reference:
            [lib:click]/core.py : BaseCommand.main()
        """
        # excerpt
        mode = 'group' if not func else 'command'
        name = func and func.__name__  # optional[str]
        desc = '' if mode == 'group' else self.commands[name]['info']['desc']
        args = None if mode == 'group' else tuple(
            x[0].upper()
            for x in self.commands[name]['info']['args']
        )
        has_args = bool(args)
        # has_args = False if mode == 'group' else bool(
        #     self.commands[name]['info']['args']
        # )
        
        console.print(
            artist.draw_title(
                prog_name=_detect_program_name(),
                commands=bool(mode == 'group'),
                arguments=args,
                serif_line=bool(desc),
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
        
        if mode == 'command' and desc:
            # console.print(indent(desc, ' ') + '\n')
            # console.print(indent(desc, ' '))
            # TEST
            from rich.text import Text
            rich_desc = Text.from_markup(indent(desc, ' '))
            rich_desc.stylize('grey74')
            console.print(rich_desc)
        
        if has_args:
            keys = (name,) if func else self.commands.keys()
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
    
    def exec(self, func, argv):
        pass


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
