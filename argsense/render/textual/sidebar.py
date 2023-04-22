import typing as t
from functools import partial

from textual.app import ComposeResult
from textual.containers import Container

from .textual_sugar import Button
from .textual_sugar import Signal
from .textual_sugar import Widget


class Sidebar(Widget):
    clicked = Signal(int, object)
    
    def __init__(self, cmd_names: t.Iterable[str]) -> None:
        super().__init__()
        self._names = cmd_names
    
    def compose(self) -> ComposeResult:
        with Container() as sidebar:
            sidebar.styles.background = '#141a20'
            sidebar.styles.padding = (1, 2)
            
            for i, name in enumerate(self._names):
                with Button(name) as item:
                    # connect(item, 'clicked', partial(self.clicked, item))
                    item.clicked.connect(
                        partial(self.clicked, i, item)
                    )
        yield sidebar
