from __future__ import annotations

import os
import sys
import typing as t

from . import config
from . import renderer
from .console import console
from .parser import FuncInfo
from .parser import parse_argv
from .parser import parse_docstring
from .parser import parse_function
from .parser.args_parser import ParamType
from .parser.args_parser import extract_command_name

__all__ = ['CommandLineInterface', 'cli']


class T:
    _FunctionId = int
    _ParamName = str
    _ParamType = ParamType
    
    Func = t.Callable
    FuncInfo = FuncInfo
    Mode = t.Literal['group', 'command']
    
    # noinspection PyTypedDict
    # FuncInfo = t.TypedDict('FuncInfo', {
    #     'func'          : Func,
    #     'cname'         : str,
    #     'desc'          : str,
    #     'args'          : t.Dict[
    #         _ParamName, t.TypedDict('ArgInfo', {
    #             'cname': str,
    #             'ctype': _ParamType,  # noqa
    #             'desc' : str,
    #         })
    #     ],
    #     'kwargs'        : t.Dict[
    #         _ParamName, t.TypedDict('ArgInfo', {
    #             'cname'  : str,
    #             'ctype'  : _ParamType,  # noqa
    #             'desc'   : str,
    #             'default': t.Any,
    #         })
    #     ],
    #     'transport_help': bool
    # })
    
    CommandsCollect = t.Dict[_FunctionId, FuncInfo]


class CommandLineInterface:
    """
    TODO: we will add group feature in future version.
    """
    
    def __init__(self, name=None):
        self.name = name
        self.commands: T.CommandsCollect = {}
        self._cname_2_func = {}
    
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
        
        func_info.target = func
        func_info.name = cmd_name
        func_info.transport_help = transport_help  # FIXME: temp solution
        func_info.fill_docs_info(docs_info)
        
        self.commands[id(func)] = func_info
    
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
                'args': {
                    k: v['ctype']
                    for k, v in (
                        {} if func_info is None
                        else func_info.args
                    ).items()
                },
                'kwargs': {
                    k: v['ctype']
                    for k, v in (
                        FuncInfo.global_kwargs() if func_info is None
                        else func_info.kwargs
                    ).items()
                },
                'index' : (
                    FuncInfo.global_cname_2_name() if func_info is None
                    else func_info.cname_2_name
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
                if '**' in func_info.kwargs:
                    if not func_info.transport_help:
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


cli = CommandLineInterface(name='argsense-cli')
