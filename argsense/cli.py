from __future__ import annotations

import os
import sys
import typing as t

from rich import print as rprint

from . import config
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
    CommandType = t.Literal['group', 'command']
    RenderMode = t.Literal['auto', 'cli', 'gui', 'tui']
    Func = t.TypeVar('Func', bound=t.Callable)
    FuncInfo = FuncInfo
    
    CommandsCollect = t.Dict[_FunctionId, FuncInfo]


class CommandLineInterface:
    """
    TODO: we will add group feature in future version.
    """
    
    def __init__(self, name: str = None) -> None:
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
        
        if (
            (cmd_name in self._cname_2_func) 
            and (new := func) is not (old := self._cname_2_func[cmd_name])
        ):
            if config.WARN_IF_DUPLICATE_COMMANDS_OVERRIDDEN:
                print(
                    ':v6pr',
                    f'duplicate command name: {cmd_name}',
                    f'the recorded function is: {old}',
                    f'the incoming function is: {new}',
                    '[yellow dim]the recorded one is kept.[/]'
                    if config.OVERWRITTEN_SCHEME == 'first'
                    else '[yellow dim]the incoming one is used.[/]'
                )
            if config.OVERWRITTEN_SCHEME == 'first':
                return
        
        self._cname_2_func[cmd_name] = func
        
        func_info = parse_function(func, fallback_type=config.FALLBACK_TYPE)
        docs_info = parse_docstring(func.__doc__ or '', func_info)
        
        func_info.target = func
        func_info.name = cmd_name
        func_info.transport_help = transport_help  # FIXME: temp solution
        func_info.fill_docs_info(docs_info)
        
        self.commands[id(func)] = func_info
    
    # -------------------------------------------------------------------------
    # decorators
    
    def cmd(self, name: str = None, transport_help: bool = False) -> T.Func:
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
        self.run(func, mode='cli')
    
    def run_gui(self, func: T.Func = None) -> None:
        self.run(func, mode='gui')
    
    def run_tui(self, func: T.Func = None) -> None:
        self.run(func, mode='tui')
    
    def run(
        self,
        func: T.Func = None,
        mode: T.RenderMode = 'auto'
    ) -> None:
        single_func_entrance = bool(func)
        
        config.apply_changes()
        cmd_type: T.CommandType = 'group' if not func else 'command'  # noqa
        
        def determine_mode() -> None:
            nonlocal mode
            if force_mode := os.getenv('ARGSENSE_UI_MODE'):
                assert force_mode in ('CLI', 'GUI', 'TUI')
                old_mode = mode.upper()
                new_mode = force_mode
                if old_mode == new_mode:
                    return
                if old_mode != 'AUTO':
                    print(
                        'argsense ui mode is force changed by environment '
                        'setting: [red]{}[/] -> [green]{}[/]'
                        .format(old_mode, new_mode),
                        ':v6p2r'
                    )
                mode = new_mode.lower()
                os.environ['ARGSENSE_UI_MODE'] = ''  # "pop" key
            else:
                if mode == 'auto':
                    mode = 'cli'
        
        determine_mode()
        
        # ---------------------------------------------------------------------
        
        def auto_detect_func_from_argv() -> t.Optional[T.Func]:
            # try to find the command name from argv
            if cmd_name := extract_command_name(sys.orig_argv):
                # print(':v', cmd_name)
                try:
                    return self._cname_2_func[cmd_name]
                except KeyError:
                    from .general import did_you_mean
                    if x := did_you_mean(cmd_name, self._cname_2_func):
                        rprint(
                            '[red]Command "{}" not found, did you mean "{}"?[/]'
                            .format(cmd_name, x)
                        )
                    else:
                        rprint(f'[red]Unknown command: {cmd_name}[/]')
                    sys.exit(1)
            return None
        
        if func is None:
            func = auto_detect_func_from_argv()
        
        # ---------------------------------------------------------------------
        
        func_info: t.Optional[T.FuncInfo] = func and self.commands[id(func)]
        
        result = parse_argv(
            argv=sys.orig_argv,
            mode=cmd_type,
            front_matter={
                'args'  : {
                    k: v['ctype']
                    for k, v in (
                        {} if func_info is None else
                        func_info.args
                    ).items()
                },
                'kwargs': {
                    k: v['ctype']
                    for k, v in (
                        FuncInfo.GLOBAL_KWARGS if func_info is None else
                        func_info.extended_kwargs
                    ).items()
                },
                'index' : (
                    FuncInfo.GLOBAL_CNAME_2_NAME if func_info is None else
                    func_info.cname_2_name
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
        
        def get_help_option(
            consider_transport_action: bool = False
        ) -> t.Tuple[bool, str, bool]:
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
        
        # print(func, mode, ':v')
        if func is None:
            has_help, help_type, is_explicit = get_help_option()
            if has_help:
                if has_help == ':helpx':
                    raise NotImplementedError
            if mode == 'cli':
                renderer.render_functions(self.commands.values())
            else:
                raise NotImplementedError(mode)
        else:
            # here, `:helpx` is downgraded to what `:help` does.
            # i.e. they have same effect, and possibly `:helpx` is an user typo.
            has_help, help_type, is_explicit = get_help_option(
                consider_transport_action=(
                    '**' in func_info.kwargs
                    and func_info.transport_help
                )
            )
            if has_help:
                if mode == 'cli':
                    renderer.render_function_parameters(
                        self.commands[id(func)],
                        show_func_name_in_title=not single_func_entrance
                    )
                else:
                    raise NotImplementedError(mode)
            else:
                try:
                    func(*result['args'].values(), **result['kwargs'])
                except Exception as e:
                    if has_help:  # DELETE: unreachable case?
                        renderer.render_function_parameters(
                            self.commands[id(func)],
                            show_func_name_in_title=not single_func_entrance
                        )
                    else:
                        raise e


cli = CommandLineInterface(name='argsense-cli')
