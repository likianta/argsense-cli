import re
import typing as t
from textwrap import dedent

import neoprint as np

from . import config
from .parser import Argv
from .parser import FuncInfo
from .parser import ParamType
from .parser import parse_argstring
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


# matches a docstring that reuses another command's parameter description.
# for example: "see `@foo:name`" (case-insensitive on the leading letter,
# with an optional trailing period after the closing backtick).
_ARGDOC_REF_PATTERN = re.compile(r'[Ss]ee\s+`@(\w+):(\w+)`\.?')


class CommandLineInterface:
    def __init__(self, name: str = None) -> None:
        self.name = name
        self.commands: T.CommandsCollect = {}
        self._cname_2_func = {}

    def __call__(self, func: T.Func) -> T.Func:
        """
        use this as decorator, to add a command.
        this is simpler than `@cli.cmd()`:
            A:
                @cli
                def foo():
                    ...
            B:
                @cli.cmd()
                def foo():
                    ...
        """
        self.add_cmd(func)
        return func

    # -------------------------------------------------------------------------

    def add_cmd(
        self, func: T.Func, name: str = '', transfer_help: bool = False
    ) -> None:
        if name:
            assert not name.startswith('-')

        from .converter import name_2_cname

        cmd_name = name or name_2_cname(func.__name__)

        if (cmd_name in self._cname_2_func) and (new := func) is not (
            old := self._cname_2_func[cmd_name]
        ):
            if config.WARN_IF_DUPLICATE_COMMANDS_OVERRIDDEN:
                np.show(
                    ':v6pr',
                    f'duplicate command name: {cmd_name}',
                    f'the recorded function is: {old}',
                    f'the incoming function is: {new}',
                    '[yellow dim]the recorded one is kept.[/]'
                    if config.OVERWRITTEN_SCHEME == 'first'
                    else '[yellow dim]the incoming one is used.[/]',
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
    # doc references

    def resolve_doc_references(self) -> None:
        """
        Resolve the parameter (and function) descriptions that reference another
        command's documentation, so that docstrings can be reused across
        commands.

        the reference is written as `see `@<cmd>:<param>`` and will be replaced
        by the target parameter's description. for example:
            @cli
            def foo(name: str):
                '''
                params:
                    name: the leader's name.
                '''

            @cli
            def bar(name: str):
                '''
                params:
                    name: see `@foo:name`
                '''

        after resolution, `bar`'s `name` description becomes "the leader's
        name.".

        note:
            - references are resolved lazily and only once per command, so the
              registration order of commands does not matter.
            - unresolved references (e.g. a non-existent command or parameter)
              are left as-is.
        """
        lookup = {fi.name: fi for fi in self.commands.values()}
        resolved: t.Set[int] = set()

        def resolve_text(text: str, stack: t.Set[int]) -> str:
            def replace(m: 're.Match[str]') -> str:
                target = lookup.get(m.group(1))
                if target is None:
                    return m.group(0)
                resolve_func(target, stack)
                param = target.get_param(m.group(2))
                if param is None:
                    return m.group(0)
                return param['desc']
            return _ARGDOC_REF_PATTERN.sub(replace, text)

        def resolve_func(func_info: T.FuncInfo, stack: t.Set[int]) -> None:
            key = id(func_info)
            if key in resolved or key in stack:  # avoid cycle and rework
                return
            stack.add(key)

            if _ARGDOC_REF_PATTERN.search(func_info.desc):
                func_info.desc = resolve_text(func_info.desc, stack)
            for args_info in (
                func_info.args0, func_info.args1,
                func_info.args2, func_info.args3, func_info.args4,
            ):
                for param in args_info.values():
                    if _ARGDOC_REF_PATTERN.search(param['desc']):
                        param['desc'] = resolve_text(param['desc'], stack)

            stack.discard(key)
            resolved.add(key)

        for func_info in self.commands.values():
            resolve_func(func_info, set())

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

    def run(self, func: T.Func = None, transport_help: bool = False) -> t.Any:
        config.apply_changes()
        return self.exec_argv(
            argv=Argv.from_sys_argv(),
            preset_func=func,
            transport_help=transport_help,
        )

    def wrap(self, func: T.Func) -> t.Callable[[], t.Any]:
        """
        Wrap a function into a zero-argument callable, which reads parameters 
        from `sys.argv` when being called.

        Note:
            - It is a simplified (and composable) version of `cli.run(func)`.
            - If `-h` / `:help` is given, the help interface is rendered and the
              target function is NOT called (returns `None`).
            - Argument parsing errors are reported and cause a `SystemExit`, the
              same as other argsense entry points.
        """
        config.apply_changes()

        func_info = parse_function(func, fallback_type=config.FALLBACK_TYPE)
        docs_info = parse_docstring(func.__doc__ or '', func_info)
        func_info.target = func
        func_info.fill_docs_info(docs_info)

        front_matter = {
            'args'  : {
                k: v['ctype'] for k, v in func_info.args.items()
            },
            'kwargs': {
                k: v['ctype'] for k, v in func_info.extended_kwargs.items()
            },
            'index' : func_info.cname_2_name,
        }

        def wrapped() -> t.Any:
            argv = Argv.from_sys_argv()
            result = parse_argv(
                argv,
                mode='command',
                front_matter=front_matter,
                implicit_help=False,  # treat "no arguments" as a real error
            )
            assert result is not None

            if result['kwargs'].get(':help'):
                from . import renderer
                renderer.render_function_parameters(
                    argv,
                    func_info,
                    show_func_name_in_title=False,
                )
                return None

            _args, _kwargs = result['args'].values(), result['kwargs']
            return func(*_args, **_kwargs)

        return wrapped

    def exec_argv(
        self,
        argv: Argv,
        preset_func: t.Optional[T.Func] = None,
        transport_help: bool = False,
        _loop_verbose: bool = True,
    ) -> t.Optional[t.Any]:
        self.resolve_doc_references()

        cli_help_form: T.CommandType
        # func_info: T.FuncInfo
        func_info: t.Optional[T.FuncInfo]

        single_func_entrance = bool(preset_func)
        cli_help_form = 'command' if preset_func else 'group'  # noqa

        func: t.Optional[t.Callable]
        if preset_func:
            func = preset_func
        else:
            if argv.possible_function:
                func = self._cname_2_func[argv.possible_function]
            else:
                func = None

        func_info = func and self.commands[id(func)]
        result = parse_argv(
            argv,
            mode=cli_help_form,
            front_matter={
                'args': {
                    k: v['ctype']
                    for k, v in (
                        {} if func_info is None else func_info.args
                    ).items()
                },
                'kwargs': {
                    k: v['ctype']
                    for k, v in (
                        FuncInfo.GLOBAL_KWARGS
                        if func_info is None
                        else func_info.extended_kwargs
                    ).items()
                },
                'index': (
                    FuncInfo.GLOBAL_CNAME_2_NAME
                    if func_info is None
                    else func_info.cname_2_name
                ),
            },
        )

        if result['command']:
            func = self._cname_2_func[result['command']]
            if func:
                func_info = self.commands[id(func)]  # noqa

        def get_help_option(
            consider_transport_action: bool = False,
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
                # FIXME: `consider_transport_action` need redesign.
                # consider_transport_action=(
                #     '**' in func_info.kwargs
                #     and func_info.transfer_help
                # )
            )
            if has_help and not transport_help:
                renderer.render_function_parameters(
                    argv,
                    self.commands[id(func)],
                    show_func_name_in_title=not single_func_entrance,
                )
            else:
                enter_func_loop = result['kwargs'].pop(':loop', False)
                _args, _kwargs = result['args'].values(), result['kwargs']
                try:
                    # noinspection PyCallingNonCallable
                    out = func(*_args, **_kwargs)
                except Exception:
                    if has_help and transport_help:
                        renderer.render_function_parameters(
                            argv,
                            self.commands[id(func)],
                            show_func_name_in_title=not single_func_entrance,
                        )
                        return
                    else:
                        raise
                if enter_func_loop:
                    flag = _loop_verbose
                    while True:
                        if flag:
                            np.show(
                                dedent(
                                    """
                                    argsense func-loop mode:
                                        1) input new args to rerun the function;
                                        2) input empty (just press enter) to -
                                        rerun function with last-time args;
                                        3) input underscore ("_") to rerun -
                                        function with original args (i.e. read -
                                        from `sys.argv`);
                                        4) input "exit" or ":q" to quit the -
                                        loop;
                                    """
                                )
                                .replace(' -\n    ', ' ')
                                .rstrip(),
                                ':v1',
                            )
                            flag = False
                        cmd = input('[argsense] input command here: ').strip()

                        if cmd == 'exit' or cmd == ':q':
                            break
                        elif cmd == '':
                            try:
                                # noinspection PyCallingNonCallable
                                out = func(*_args, **_kwargs)
                            except Exception:
                                np.show(':e')
                        else:
                            if cmd == '_':
                                new_argv = Argv.from_sys_argv()
                                assert ':loop' in new_argv.args
                            else:
                                try:
                                    new_args = parse_argstring(cmd)
                                except Exception:
                                    np.show(':e')
                                    continue
                                else:
                                    new_args.append(':loop')
                                new_argv = Argv(
                                    argv.launcher,
                                    argv.target,
                                    new_args,  # type: ignore
                                )
                            return self.exec_argv(
                                argv=new_argv,
                                preset_func=func,
                                _loop_verbose=False,
                            )
                return out
        else:
            has_help, is_explicit = get_help_option()
            assert has_help
            renderer.render_functions(argv, self.commands.values())


cli = CommandLineInterface(name='argsense-cli')
