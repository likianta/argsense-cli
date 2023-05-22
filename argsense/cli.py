from __future__ import annotations

import os
import sys
import typing as t

from . import config
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
    
    # TODO: use 'grp', 'cmd' instead?
    CmdMode = t.Literal['group', 'command']
    TuiMode = t.Literal['auto', 'close', 'force']
    Func = t.Callable
    FuncInfo = FuncInfo
    
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
    
    def run_cli(self, func: T.Func = None) -> None:
        self.run(func, tui_mode='close')
    
    def run_tui(self, func: T.Func = None) -> None:
        self.run(func, tui_mode='force')
    
    def run(
            self,
            func: T.Func = None,
            tui_mode: T.TuiMode = 'auto'
    ) -> None:
        config.apply_changes()
        cmd_mode: T.CmdMode = 'group' if not func else 'command'  # noqa
        
        def update_ui_mode() -> None:
            nonlocal tui_mode
            if force_mode := os.getenv('ARGSENSE_UI_MODE'):
                assert force_mode in ('CLI', 'TUI')
                old_mode = {'force': 'TUI', 'close': 'CLI',
                            'auto' : 'auto'}[tui_mode]
                new_mode = force_mode
                if old_mode == new_mode:
                    return
                if old_mode != 'auto':
                    print(
                        'argsense ui mode is force changed by environment '
                        'variable: [red]{}[/] -> [green]{}[/]'.format(
                            old_mode, new_mode
                        ), ':v3sp2r'
                    )
                tui_mode = 'force' if new_mode == 'TUI' else 'close'
                os.environ['ARGSENSE_UI_MODE'] = ''  # "pop" key
        
        update_ui_mode()
        
        # ---------------------------------------------------------------------
        
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
        
        if func is None:
            func = auto_detect_func_from_argv()
        
        # ---------------------------------------------------------------------
        
        func_info: t.Optional[T.FuncInfo]
        func_info = func and self.commands[id(func)]
        
        result = parse_argv(
            argv=sys.argv,
            mode=cmd_mode,
            front_matter={
                'args'  : {
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
        
        # ---------------------------------------------------------------------
        from . import renderer
        
        def get_help_option(consider_transport_action=False) \
                -> t.Tuple[bool, str, bool]:
            """
            return: (has_help, help_type, is_explicit)
            """
            has_implicit = False
            if ':helpx' in result['kwargs'] or ':help' in result['kwargs']:
                for h in (':helpx', ':help'):
                    if h in result['kwargs']:
                        if result['kwargs'][h]:  # explicit
                            if consider_transport_action:
                                return False, h, True
                            return True, h, True
                        else:  # implicit, continue to check next
                            has_implicit = True
                            continue
                if has_implicit:
                    return True, ':help', False
                else:
                    return False, '', False
            else:
                return False, '', False
        
        def call_func() -> None:
            try:
                func(*result['args'].values(), **result['kwargs'])
            except Exception:
                # console.print_exception()
                if ':helpx' in result['kwargs'] or ':help' in result['kwargs']:
                    renderer.render_cli(
                        self, func, show_func_name_in_title=True
                    )
                else:
                    console.print_exception()
        
        # PERF: the spaghetti code is ugly.
        # print(func, ':v')
        if func is None:
            if tui_mode == 'force':
                renderer.launch_tui(tuple(self.commands.values()))
            elif tui_mode == 'close':
                if ':helpx' in result['kwargs']:
                    renderer.render_cli_2(self)
                else:
                    renderer.render_cli(
                        self, func, show_func_name_in_title=bool(
                            cmd_mode == 'group'
                        )
                    )
            # else:
            #     """
            #     # if user explicitly passes `--help` or `-h`
            #     argsense xxx.py -h  # turn off TUI mode and show CLI panel
            #     argsense xxx.py     # launch TUI
            #     """
            #     has_help, help_type, is_explicit = get_help_option()
            #     if has_help:
            #         if is_explicit:
            #             if help_type == ':helpx':
            #                 renderer.render_cli_2(self)
            #             else:
            #                 renderer.render_cli(
            #                     self, func, show_func_name_in_title=bool(
            #                         cmd_mode == 'group'
            #                     )
            #                 )
            #             return
            #     renderer.launch_tui(tuple(self.commands.values()))
            else:
                # [2023-04-27] do not use TUI mode
                has_help, help_type, is_explicit = get_help_option()
                if has_help:
                    if has_help == ':helpx':
                        renderer.render_cli_2(self)
                        return
                # fallback to CLI `:help`
                renderer.render_cli(
                    self, func, show_func_name_in_title=bool(
                        cmd_mode == 'group'
                    )
                )
        else:
            # here, `:helpx` is downgraded to what `:help` does.
            # i.e. they have same effect, and possibly `:helpx` is an user typo.
            if tui_mode == 'force':
                renderer.launch_tui((func_info,))
                return
            has_help, help_type, is_explicit = get_help_option(
                consider_transport_action=(
                        '**' in func_info.kwargs
                        and func_info.transport_help
                )
            )
            if tui_mode == 'close':
                if has_help:
                    renderer.render_cli(
                        self, func, show_func_name_in_title=True
                    )
                else:
                    call_func()
            # else:
            #     if has_help:
            #         if is_explicit:
            #             # ignore `help_type`, because they have same effect.
            #             renderer.render_cli(
            #                 self, func, show_func_name_in_title=True
            #             )
            #         else:
            #             renderer.launch_tui((func_info,))
            #     else:
            #         call_func()
            else:
                if has_help:
                    # ignore `help_type`, because they have same effect.
                    renderer.render_cli(
                        self, func, show_func_name_in_title=True
                    )
                else:
                    call_func()


cli = CommandLineInterface(name='argsense-cli')
