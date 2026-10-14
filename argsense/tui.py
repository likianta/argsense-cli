import sys
import typing as tp

from . import config
from .cli import CommandLineInterface
from .cli import T as T0


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
        interface = self._interface
        preset_func = interface.prepare_entrance(entrance, sys._getframe(1))
        interface.resolve_doc_references()

        if preset_func is not None:
            func_info = interface.commands[id(preset_func)]
        else:
            funcs = list(interface.commands.values())
            if len(funcs) != 1:
                raise RuntimeError(
                    'the tui interface works on exactly one command, but '
                    '{} were given: {}'.format(
                        len(funcs), ', '.join(f.name for f in funcs)
                    )
                )
            func_info = funcs[0]

        from .renderer.tui import run_form

        return run_form(func_info, inline=inline)


tui = TuiInterface(name='argsense-tui')
