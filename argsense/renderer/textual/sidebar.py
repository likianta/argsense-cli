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
        self.styles.width = 'auto'
        self.styles.min_width = 20
        self.styles.max_width = 40
        
        with Container() as sidebar:
            sidebar.styles.width = self._get_proper_width()
            sidebar.styles.background = '#141a20'
            sidebar.styles.padding = (1, 1)
            
            for i, name in enumerate(self._names):
                with Button(name) as item:
                    item.styles.width = '100%'
                    item.clicked.connect(
                        partial(self.clicked, i, item)
                    )
        yield sidebar
        
    def _get_proper_width(self) -> int:
        return max(len(x) for x in self._names) + 4
