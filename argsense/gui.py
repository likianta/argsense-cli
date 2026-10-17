import sys
import typing as tp

from . import config
from .cli import CommandLineInterface
from .cli import DEFAULT_GUI_PORT
from .cli import T as T0
from .parser import Argv


class GraphicalUserInterface:
    """
    The graphical (GUI) form of the command line interface.

    It *uses* a `CommandLineInterface` to share the registration, the
    signature parsing and the docstring workflow, but renders an editable form
    in the browser (or in a native window) instead of parsing `sys.argv`.

    Usage:
        from argsense import gui

        def main(name: str, age: int):
            ...

        gui.run(main)
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

    def run(
        self,
        entrance: T0.Entrance = None,
        window: bool = False,
        port: int = DEFAULT_GUI_PORT,
        title: str = 'argsense',
    ) -> tp.Any:
        """
        Note:
            Every registered command gets a pane of its own in the form, and
            Run calls the one on show. Pass `window=True` to open the form in
            a native window instead of serving it for a browser tab.
        """
        config.apply_changes()
        return self._interface.run_gui(
            entrance,
            sys._getframe(1),
            argv=Argv.from_sys_argv(),
            window=window,
            port=port,
            title=title,
        )


gui = GraphicalUserInterface(name='argsense-gui')
