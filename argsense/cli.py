import sys
import typing as t

from . import config
from .parser import Argv
from .parser import FuncInfo
from .parser import ParamType
from .parser import parse_argv
from .parser import parse_docstring
from .parser import parse_function


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
        transfer_help: bool = False,
    ) -> None:
        if name:
            assert not name.startswith('-')
        
        from .converter import name_2_cname
        
        cmd_name = name or name_2_cname(func.__name__)
        
        if (
            (cmd_name in self._cname_2_func) and
            (new := func) is not (old := self._cname_2_func[cmd_name])
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
        func_info.transfer_help = transfer_help  # FIXME: temp solution
        func_info.fill_docs_info(docs_info)
        
        self.commands[id(func)] = func_info
    
    # -------------------------------------------------------------------------
    # decorators
    
    def cmd(self, name: str = None, transfer_help: bool = False) -> T.Func:
        """
        usage:
            from argsense import cli
            @cli.cmd()
            def foo(...):
                ...
        """
        
        def decorator(func: T.Func) -> T.Func:
            self.add_cmd(func, name, transfer_help)
            return func
        
        return decorator
    
    # -------------------------------------------------------------------------
    # run
    
    def run(self, func: T.Func = None) -> t.Any:
        config.apply_changes()
        return self.exec_argv(
            argv=Argv.from_sys_argv(
                sys.orig_argv if hasattr(sys, 'orig_argv') else
                (sys.executable, *sys.argv)
            ),
            func=func
        )
        
    def exec_argv(
        self, argv: Argv, func: t.Optional[T.Func] = None
    ) -> t.Optional[t.Any]:
        cli_help_form: T.CommandType
        # func_info: T.FuncInfo
        func_info: t.Optional[T.FuncInfo]
        
        single_func_entrance = bool(func)
        cli_help_form = 'command' if func else 'group'  # noqa
        
        if not func:
            if argv.possible_function:
                func = self._cname_2_func[argv.possible_function]
        
        func_info = func and self.commands[id(func)]
        result = parse_argv(
            argv,
            mode=cli_help_form,
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
        print(result, ':vl')
        
        if result['command']:
            func = self._cname_2_func[result['command']]
            if func:
                func_info = self.commands[id(func)]
        
        def get_help_option(
            consider_transport_action: bool = False
        ) -> t.Tuple[bool, bool]:
            """
            return: (has_help, is_explicit)
            """
            has_help = ':help' in result['kwargs']
            is_explicit = result['kwargs'][':help'] if has_help else False
            
            if is_explicit:
                if consider_transport_action:
                    return False, True
                else:
                    return True, True
            else:
                if has_help:
                    return True, False
                else:
                    return False, False
        
        from . import renderer
        if func:
            has_help, is_explicit = get_help_option(
                consider_transport_action=(
                    '**' in func_info.kwargs
                    and func_info.transfer_help
                )
            )
            if has_help:
                renderer.render_function_parameters(
                    self.commands[id(func)],
                    show_func_name_in_title=not single_func_entrance
                )
            else:
                return func(*result['args'].values(), **result['kwargs'])
        else:
            has_help, is_explicit = get_help_option()
            assert has_help
            renderer.render_functions(self.commands.values())


cli = CommandLineInterface(name='argsense-cli')
