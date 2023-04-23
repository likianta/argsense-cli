from __future__ import annotations

import os
import sys
import typing as t

from . import config
from . import renderer
from .argparse import ParamType
from .argparse import extract_command_name
from .argparse import parse_argv
from .console import console
from .parser import parse_docstring
from .parser import parse_function

__all__ = ['CommandLineInterface', 'cli']


class T:
    _FunctionId = int
    _ParamName = str
    _ParamType = ParamType
    Func = t.Callable
    
    # noinspection PyTypedDict
    FuncInfo = t.TypedDict('FuncInfo', {
        'func'          : Func,
        'cname'         : str,
        'desc'          : str,
        'args'          : t.Dict[
            _ParamName, t.TypedDict('ArgInfo', {
                'cname': str,
                'ctype': _ParamType,  # noqa
                'desc' : str,
            })
        ],
        'kwargs'        : t.Dict[
            _ParamName, t.TypedDict('ArgInfo', {
                'cname'  : str,
                'ctype'  : _ParamType,  # noqa
                'desc'   : str,
                'default': t.Any,
            })
        ],
        'transport_help': bool
    })
    Mode = t.Literal['group', 'command']
    
    CommandsCollect = t.Dict[_FunctionId, FuncInfo]


class CommandLineInterface:
    """
    TODO: we will add group feature in future version.
    """
    
    def __init__(self, name=None):
        self.name = name
        self.commands: T.CommandsCollect = {}
        self._cname_2_func = {}
        self._global_options = GlobalOptions()
    
    # -------------------------------------------------------------------------
    
    def add_cmd(
            self,
            func: T.Func,
            name: str = None,
            transport_help: bool = False
    ) -> None:
        if name:
            assert not name.startswith('-')
        
        from .converter import name_2_cname
        from .converter import type_2_ctype
        
        cmd_name = name or name_2_cname(func.__name__)
        if cmd_name in self._cname_2_func and \
                (new := func) is not (old := self._cname_2_func[cmd_name]):
            print(
                ':v3p',
                f'duplicate command name: {cmd_name}',
                f'the recorded function is: {old}',
                f'the incoming function is: {new}',
            )
            if config.OVERWRITTEN_SCHEME == 'first':
                print(':v3pr', '[yellow dim]the recorded one is keeped.[/]')
                return
            else:
                print(':v3pr', '[yellow dim]the incoming one is used.[/]')
        self._cname_2_func[cmd_name] = func
        
        func_info = parse_function(func, fallback_type=config.FALLBACK_TYPE)
        docs_info = parse_docstring(func.__doc__ or '')
        
        # noinspection PyTypeChecker
        self.commands[id(func)] = {
            'func'          : func,
            'cname'         : cmd_name,
            'desc'          : docs_info['desc'],
            'args'          : {
                name: {
                    'cname': name_2_cname(name, style='arg'),
                    'ctype': type_2_ctype(type_),
                    'desc' : (
                        '' if name not in docs_info['args']
                        else docs_info['args'][name]['desc']
                    ),
                } for name, type_ in func_info['args']
            },
            'kwargs'        : {
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
            'transport_help': transport_help,
        }
    
    # -------------------------------------------------------------------------
    # decorators
    
    def cmd(self, name: str = None, transport_help=False) -> T.Func:
        """
        usage:
            from argsense import cli
            @cli.cmd()
            def foo(...):
                ...
        """
        
        def decorator(func: T.Func) -> T.Func:
            self.add_cmd(func, name, transport_help)
            return func
        
        return decorator
    
    # -------------------------------------------------------------------------
    # run
    
    def run(self, func=None) -> None:
        config.apply_changes()
        cmd_mode: T.Mode = 'group' if not func else 'command'  # noqa
        tui_mode = os.getenv('ARGSENSE_TUI')  # bool-like type
        
        def auto_detect_func_from_argv() -> t.Optional[T.Func]:
            # try to find the command name from argv
            if cmd_name := extract_command_name(sys.argv):
                # print(':v', cmd_name)
                try:
                    return self._cname_2_func[cmd_name]
                except KeyError:
                    from .general import did_you_mean
                    if x := did_you_mean(cmd_name, self._cname_2_func):
                        console.print('[red]Command "{}" not found, did you '
                                      'mean "{}"?[/]'.format(cmd_name, x))
                    else:
                        console.print(f'[red]Unknown command: {cmd_name}[/]')
                    sys.exit(1)
            return None
        
        func = auto_detect_func_from_argv()
        
        # ---------------------------------------------------------------------
        
        func_info: t.Optional[T.FuncInfo]
        func_info = func and self.commands[id(func)]
        
        result = parse_argv(
            argv=sys.argv,
            mode=cmd_mode,
            front_matter={
                'args'  : {} if func is None else {
                    k: v['ctype']
                    for k, v in func_info['args'].items()
                },
                'kwargs': (
                    self._global_options.name_2_type if func is None
                    else {
                        **self._global_options.name_2_type,
                        **{k: v['ctype']
                           for k, v in func_info['kwargs'].items()}
                    }
                ),
                'index' : (
                    self._global_options.cname_2_name if func is None
                    else {
                        **self._global_options.cname_2_name,
                        **{n: k
                           for k, v in func_info['kwargs'].items()
                           for n in v['cname'].split(',')}
                    }
                )
            }
        )
        # print(':lv', result)
        
        if result['command']:
            func = self._cname_2_func[result['command']]
            if func:
                func_info = self.commands[id(func)]
        
        if func is None:
            # NOTE: we take `--help` as the most important option to check.
            #   currently `--help` and `--helpx` are the only two global
            #   options.
            if tui_mode:
                renderer.launch_tui(tuple(self.commands.values()))
            else:
                if result['kwargs'].get(':helpx'):
                    renderer.render_cli_2(self)
                else:
                    renderer.render_cli(
                        self, func, show_func_name_in_title=bool(
                            cmd_mode == 'group'
                        )
                    )
        else:
            if result['kwargs'].get(':help') or \
                    result['kwargs'].get(':helpx'):
                if '**' in func_info['kwargs']:
                    if not func_info['transport_help']:
                        if tui_mode:
                            renderer.launch_tui((func_info,))
                        else:
                            renderer.render_cli(
                                self, func, show_func_name_in_title=True
                            )
                        return
                else:
                    if tui_mode:
                        renderer.launch_tui((func_info,))
                    else:
                        renderer.render_cli(
                            self, func, show_func_name_in_title=True
                        )
                    return
            
            try:
                func(*result['args'].values(), **result['kwargs'])
            except Exception:
                # console.print_exception()
                if (
                        result['kwargs'].get(':help') or
                        result['kwargs'].get(':helpx')
                ):
                    renderer.render_cli(self, func, show_func_name_in_title=True)
                else:
                    console.print_exception()


class GlobalOptions:
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
    
    name_2_type = {
        ':help' : ParamType.FLAG,
        ':helpx': ParamType.FLAG,
    }


cli = CommandLineInterface(name='argsense-cli')
