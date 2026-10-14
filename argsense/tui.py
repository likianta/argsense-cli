import sys
import typing as tp

from . import config
from .cli import CommandLineInterface
from .cli import T as T0
from .parser import Argv


class TuiInterface:
    """
    The textual (TUI) form of the command line interface.

    It *uses* a `CommandLineInterface` to share the registration, the
    signature parsing and the docstring workflow, but renders an editable form
    instead of parsing `sys.argv`.

    Usage:
        from argsense import tui

        def main(name: str, age: int):
            ...

        tui.run(main)
    """

    def __init__(self, name: tp.Optional[str] = None) -> None:
        self._interface = CommandLineInterface(name)

    @property
    def commands(self) -> T0.CommandsCollect:
        return self._interface.commands

    def __call__(self, func: T0.Func) -> T0.Func:
        """use this as decorator, to add a command."""
        self._interface.add_cmd(func)
        return func

    def add_cmd(self, func: T0.Func, name: str = '') -> None:
        """add a command."""
        self._interface.add_cmd(func, name)

    def run(self, entrance: T0.Entrance = None, inline: bool = False) -> tp.Any:
        """
        Note:
            Only a single command is supported here. Passing several commands
            raises a `RuntimeError`.
        """
        config.apply_changes()
        func_info = self._interface.resolve_single_command(
            entrance, sys._getframe(1)
        )

        from .renderer.tui import run_form

        argv = Argv.from_sys_argv()
        return run_form(
            func_info,
            inline=inline,
            argv=argv,
            cli_runner=lambda tokens: self._interface.exec_argv(
                Argv(argv.launcher, argv.target, tokens),
                preset_func=func_info.target,
            ),
        )


tui = TuiInterface(name='argsense-tui')
