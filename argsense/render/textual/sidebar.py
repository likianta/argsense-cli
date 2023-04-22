import typing as t
from functools import partial

from textual.app import ComposeResult

from .textual_sugar import Button
from .textual_sugar import Container
from .textual_sugar import Signal


class Sidebar(Container):
    clicked: Signal
    
    def __init__(self, cmd_names: t.Iterable[str]) -> None:
        super().__init__()
        self._names = cmd_names
    
    def compose(self) -> ComposeResult:
        # with Container() as sidebar:
        self.styles.background = '#141a20'
        self.styles.padding = (1, 2)
        for name in self._names:
            with Button(name) as item:
                # connect(item, 'clicked', partial(self.clicked, item))
                item.clicked.connect(
                    partial(self.clicked, item)
                )
            yield item
