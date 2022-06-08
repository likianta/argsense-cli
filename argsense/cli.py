from __future__ import annotations

import os
import sys
import typing as t
from textwrap import indent

from . import artist
from .argparse import ParamType
from .console import console
from .parser import parse_docstring
from .parser import parse_function

__all__ = ['cli', 'CommandLineInterface']


class T:
    Mode = t.Literal['group', 'command']
    
    _FunctionId = int
    _ParamName = str
    _ParamType = ParamType
    CommandsCollect = t.Dict[
        _FunctionId, t.TypedDict('FuncInfo', {
            'func'  : t.Callable,
            'cname' : str,
            'desc'  : str,
            'args'  : t.Dict[
                _ParamName, t.TypedDict('ArgInfo', {
                    'cname': str,
                    'ctype': _ParamType,  # noqa
                    'desc' : str,
                })
            ],
            'kwargs': t.Dict[
                _ParamName, t.TypedDict('ArgInfo', {
                    'cname'  : str,
                    'ctype'  : _ParamType,  # noqa
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
    
    def __init__(self, name=None):
        self.name = name
        self.commands: T.CommandsCollect = {}
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
                        'desc' : (
                            '' if name not in docs_info['args']
                            else docs_info['args'][name]['desc']
                        ),
                    } for name, type_ in func_info['args']
                },
                'kwargs': {
                    name: {
                        'cname'  : (
                            name_2_cname(name, style='opt')
                            if name not in docs_info['kwargs']
                            else docs_info['kwargs'][name]['cname']
                        ),
                        'ctype'  : type_2_ctype(type_),
                        'desc'   : (
                            '' if name not in docs_info['kwargs']
                            else docs_info['kwargs'][name]['desc']
                        ),
                        'default': value,
                    } for name, type_, value in func_info['kwargs']
                },
            }
            
            return func
        
        return decorator
    
    # -------------------------------------------------------------------------
    # run
    
    class GlobalOptions:
        name_2_type = {
            ':help' : ParamType.FLAG,
            ':helpx': ParamType.FLAG,
        }
        
        cname_2_name = {
            '--:help' : ':help',
            '-:h'     : ':help',
            '--help'  : ':help',
            '-h'      : ':help',
            '--:helpx': ':helpx',
            '-:hh'    : ':helpx',
            '--helpx' : ':helpx',
            '-hh'     : ':helpx',
        }
    
    def run(self, func=None):
        from . import config
        from .argparse import extract_command_name, parse_argv
        
        config.apply_changes()
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
                'kwargs': (
                    self.GlobalOptions.name_2_type if func is None
                    else {
                        **self.GlobalOptions.name_2_type,
                        **{k: v['ctype']
                           for k, v in self.commands[
                               id(func)]['kwargs'].items()}
                    }
                ),
                'index' : (
                    self.GlobalOptions.cname_2_name if func is None
                    else {
                        **self.GlobalOptions.cname_2_name,
                        **{n: k
                           for k, v in self.commands[
                               id(func)]['kwargs'].items()
                           for n in v['cname'].split(',')}
                    }
                ),
            }
        )
        # print(':lv', result)
        if result['command']:
            func = self._cname_2_func[result['command']]
        # FIXME: we take '--help' as the most important option to check. the
        #   '--help' is the only global option for now.
        if not result['args'] and not result['kwargs']:
            if self.commands[id(func)]['args'] \
                    or self.commands[id(func)]['kwargs']:
                result['kwargs'][':help'] = True
        if result['kwargs'].get(':help'):
            self.show(func)
        elif result['kwargs'].get(':helpx'):
            if func:
                self.show(func)
            else:
                self.show2()
                # # self.show(None)
                # # for func_info in self.commands.values():
                # #     self.show(func_info['func'])
        else:
            self.exec(func, result['args'], result['kwargs'])
    
    def show(self, func):
        """
        reference:
            [lib:click]/core.py : BaseCommand.main()
        """
        is_group: bool
        has_args: bool
        has_kwargs: bool
        
        if func is None:
            is_group = True
            has_args = False
            has_kwargs = False
            
            console.print(
                artist.draw_title(
                    prog_name=_detect_program_name(),
                    command='<COMMAND>',
                    arguments=None,
                ),
                justify='center'
            )
            
            console.print(
                artist.draw_commands_panel((
                    (v['cname'], v['desc'])
                    for v in self.commands.values()
                ))
            )
        
        else:
            func_info = self.commands[id(func)]
            desc = func_info['desc']
            is_group = False
            has_args = bool(func_info['args'])
            has_kwargs = bool(func_info['kwargs'])
            
            # experimental
            if has_args and has_kwargs:
                from .config import Dynamic
                Dynamic.PREFERRED_FIELD_WIDTH_OF_NAME = max((
                    *map(len, (x['cname']
                               for x in func_info['args'].values())),
                    *map(len, (x['cname'].replace(',', ', ')
                               for x in func_info['kwargs'].values())),
                ))
                # print(Dynamic.PREFERRED_FIELD_WIDTH_OF_NAME, ':v')
            
            console.print(
                artist.draw_title(
                    prog_name=_detect_program_name(),
                    command=func_info['cname'],
                    arguments=tuple(
                        v['cname'] for v in func_info['args'].values()
                    ),
                ),
                justify='center'
            )
            if desc:
                console.print(indent(desc, ' '))
            
            if args := func_info['args']:
                console.print(
                    artist.draw_arguments_panel((
                        (v['cname'], v['ctype'].name, v['desc'])
                        for v in args.values()
                    ))
                )
            
            if kwargs := func_info['kwargs']:
                console.print(
                    artist.draw_options_panel((
                        (v['cname'].replace(',', ', '),
                         v['ctype'].name,
                         v['desc'],
                         '[red dim](default={})[/]'.format(v['default']))
                        for v in kwargs.values()
                    ))
                )
        
        # show logo in right-bottom corner.
        if not is_group and not has_args and not has_kwargs:
            return
        # noinspection PyTypeChecker
        console.print(
            artist.post_logo(
                style='magenta' if is_group
                else 'white' if has_kwargs
                else 'blue'
            ),
            justify='right', style='bold', end=' \n'
        )
    
    def show2(self):
        """
        warning: this is an experimental method for testing new style of 'helpx'.
        """
        from rich.align import Align
        from rich.padding import Padding
        
        def show(func: t.Optional[t.Callable], show_logo: bool) -> dict:
            is_group: bool
            has_args: bool
            has_kwargs: bool
            
            collect_renderables = {
                'title'    : None,
                'desc'     : None,
                'cmd_panel': None,
                'arg_panel': None,
                'opt_panel': None,
                'logo'     : None,
            }
            
            if func is None:
                is_group = True
                has_args = False
                has_kwargs = False
                
                collect_renderables['title'] = Align.center(
                    artist.draw_title(
                        prog_name=_detect_program_name(),
                        command='<COMMAND>',
                        arguments=None,
                    )
                )
                
                collect_renderables['cmd_panel'] = (
                    artist.draw_commands_panel((
                        (v['cname'], v['desc'])
                        for v in self.commands.values()
                    ))
                )
            
            else:
                func_info = self.commands[id(func)]
                desc = func_info['desc']
                is_group = False
                has_args = bool(func_info['args'])
                has_kwargs = bool(func_info['kwargs'])
                
                # experimental
                if has_args and has_kwargs:
                    from .config import Dynamic
                    Dynamic.PREFERRED_FIELD_WIDTH_OF_NAME = max((
                        *map(len, (x['cname']
                                   for x in func_info['args'].values())),
                        *map(len, (x['cname'].replace(',', ', ')
                                   for x in func_info['kwargs'].values())),
                    ))
                
                collect_renderables['title'] = Align.center(
                    artist.draw_title(
                        prog_name=_detect_program_name(),
                        command=func_info['cname'],
                        arguments=tuple(
                            v['cname'] for v in func_info['args'].values()
                        ),
                    )
                )
                if desc:
                    collect_renderables['desc'] = indent(desc, ' ')
                
                if args := func_info['args']:
                    collect_renderables['arg_panel'] = (
                        artist.draw_arguments_panel((
                            (v['cname'], v['ctype'].name, v['desc'])
                            for v in args.values()
                        ))
                    )
                
                if kwargs := func_info['kwargs']:
                    collect_renderables['opt_panel'] = (
                        artist.draw_options_panel((
                            (v['cname'].replace(',', ', '),
                             v['ctype'].name,
                             v['desc'],
                             '[red dim](default={})[/]'.format(v['default']))
                            for v in kwargs.values()
                        ))
                    )
            
            # show logo in right-bottom corner.
            if show_logo:
                if not is_group and not has_args and not has_kwargs:
                    return collect_renderables
                # noinspection PyTypeChecker
                collect_renderables['logo'] = Padding(
                    Align.right(
                        artist.post_logo(
                            style='magenta' if is_group
                            else 'white' if has_kwargs
                            else 'blue'
                        ), style='bold'
                    ), (0, 1, 0, 0)
                )
            
            return collect_renderables
        
        parts = []  # noqa
        parts.append(show(None, show_logo=True))
        parts.extend(show(v['func'], show_logo=False)
                     for v in self.commands.values())
        
        def render():
            # from rich.columns import Columns
            from rich.console import Group
            from rich.panel import Panel
            
            # preferred_field_width = {
            #     'command_field': max(
            #         map(len, (v['cname']
            #                   for v in self.commands.values()))
            #     ),
            #     'param_field'  : max((
            #         *map(len, (w['cname']
            #                    for v in self.commands.values()
            #                    for w in v['args'].values())),
            #         *map(len, (w['cname'].replace(',', ', ')
            #                    for v in self.commands.values()
            #                    for w in v['kwargs'].values())),
            #     )),
            #     'type_field'   : len('NUMBER'),
            # }
            # print(preferred_field_width, ':v')
            
            def tint(text: str, color: str) -> str:
                # a simple function to tint a text snippet.
                return f'[{color}]{text}[/]'
            
            console.print(parts[0]['title'])
            assert not parts[0]['desc']
            
            group = []
            for index, func_info in enumerate(self.commands.values()):
                # # cmd_name = func_info['cname']
                # # cmd_desc = func_info['desc']
                # # col = Columns((
                # #     tint(cmd_name.ljust(
                # #         preferred_field_width['command_field']
                # #     ), 'magenta'),
                # #     cmd_desc
                # # ), padding=(0, 4))
                # # # TODO: how to highlight its background in the full console
                # # #   width?
                # # # from rich.box import Box
                # # # col = Panel(col, box=Box(''), style='default on yellow')
                # # group.append(col)
                cmd_name = func_info['cname']
                group.append(tint(f' {cmd_name} ', 'b dark_magenta on yellow'))
                
                sub_part = parts[index + 1]
                sub_panel = Padding(Panel(
                    Group(*filter(
                        lambda x: x is not None,
                        (
                            # sub_part['title'],
                            sub_part['desc'],
                            sub_part['arg_panel'],
                            sub_part['opt_panel'],
                        )
                    )),
                    border_style='#f49364',  # dim | #f49364
                    title=str(sub_part['title']).split('\\n')[1].replace(
                        '\\[OPTIONS]', '[OPTIONS]'
                    ),
                    title_align='center',
                ), pad=(0, 0, 0, 4))
                group.append(sub_panel)
                
                group.append('')
            
            assert group[-1] == ''
            group[-1] = parts[0]['logo']
            
            # TODO: (below) both A and B are good, i would make it customizable
            #   in the future.
            return Panel(Group(*group), border_style='magenta')  # A
            # return Group(*group)  # B
        
        console.print(render())
    
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


cli = CommandLineInterface(name='argsense-cli')
