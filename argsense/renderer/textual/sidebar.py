import typing as t
from functools import partial

from textual.app import ComposeResult
from textual.widgets import Static

from .textual_sugar import Button
from .textual_sugar import Container
from .textual_sugar import Signal
from .textual_sugar import Widget


class Sidebar(Widget):
    clicked = Signal(int, 'MyItem')
    control: Container
    _last_index: int = 0
    
    def __init__(self, cmd_names: t.Iterable[str]) -> None:
        super().__init__()
        self._names = cmd_names
        self.clicked.connect(self._update_item_focus_style)
    
    def compose(self) -> ComposeResult:
        self.styles.width = 'auto'
        # self.styles.width = self._get_proper_width()
        self.styles.min_width = 20
        self.styles.max_width = 40
        
        with Container() as sidebar:
            proper_width = self._get_proper_width()
            sidebar.styles.width = proper_width
            sidebar.styles.background = '#141a20'
            sidebar.styles.padding = (1, 1)
            
            for i, name in enumerate(self._names):
                with MyItem(i, name, proper_width - 2) as item:
                    item.styles.width = '100%'
                    item.clicked.connect(
                        partial(self.clicked, i, item)
                    )
                # if i == 0: item.activate()
        self.control = sidebar
        yield sidebar
    
    def _get_proper_width(self) -> int:
        return max(len(x) for x in self._names) + 8
    
    def _update_item_focus_style(self, idx: int, item: 'MyItem') -> None:
        if idx == self._last_index: return
        item.activate()
        last_item = t.cast(MyItem, self.control.children[self._last_index])
        last_item.deactivate()
        self._last_index = idx


# -----------------------------------------------------------------------------

class MyItem(Container):
    clicked = Signal()
    # _bg = t.cast(str, Reactive(''))
    _indicator: Static
    
    def __init__(self, index: int, label: str, predefined_width) -> None:
        super().__init__()
        self.index = index
        self.label = label
        self._predefined_width = predefined_width
    
    def activate(self) -> None:
        # self.label = ':point_right: ' + self._label
        # self._indicator.visible = True
        self._indicator.update(':point_right:')
    
    def deactivate(self) -> None:
        # self.label = self._label
        # self._indicator.visible = False
        self._indicator.update(f'{self.index + 1}')
    
    def compose(self) -> ComposeResult:
        # self.styles.layers = ('base', 'floating')
        self.styles.width = self._predefined_width
        self.styles.height = 3
        self.styles.layout = 'horizontal'
        self.styles.content_align_vertical = 'middle'
        
        with Static(f'{self.index + 1}') as indicator:
            # indicator.styles.layer = 'floating'
            indicator.styles.width = 3
            indicator.styles.height = 3
            # indicator.styles.background = btn.styles.color
            indicator.styles.content_align_vertical = 'middle'
            # indicator.styles.margin = 1
        
        self._indicator = indicator
        if self.index == 0:
            self.activate()
        
        with Button(self.label) as btn:
            # btn.styles.layer = 'base'
            # btn.styles.width = '100%'
            # btn.styles.width = 'auto'
            btn.styles.width = self._predefined_width - 3
            btn.styles.height = 3
            # btn.styles.dock = 'right'
            # btn.styles.padding = (0, 0, 0, 2)
            btn.clicked.connect(self.clicked)
        
        yield btn
        yield indicator
    
    # def watch__bg(self, bg: str):
    #     self._indicator.styles.background = bg


class MyItem2(Button):  # DELETE
    clicked = Signal()
    _indicator: Static
    
    # def __init__(self, label: str) -> None:
    #     super().__init__(label)
    #     self._label = label
    
    # noinspection PyTypeChecker
    def activate(self) -> None:
        # self.label = ':point_right: ' + self._label
        self._indicator.visible = True
    
    # noinspection PyTypeChecker
    def deactivate(self) -> None:
        # self.label = self._label
        self._indicator.visible = False
    
    def compose(self) -> ComposeResult:
        # self.styles.height = 3
        self.styles.layers = ('base', 'floating')
        with Static(':point_right:') as indicator:
            indicator.styles.layer = 'floating'
            indicator.styles.width = 2
            indicator.styles.height = 3
            indicator.styles.content_align_vertical = 'middle'
            indicator.styles.background = 'transparent'
            indicator.visible = False
        self._indicator = indicator
        
        yield indicator


class MyItem3(Button):
    clicked = Signal()
    label: str
    
    def __init__(self, label: str) -> None:
        super().__init__(label)
        self._label = label
    
    def activate(self) -> None:
        self.label = ':point_right: ' + self._label
    
    def deactivate(self) -> None:
        self.label = self._label
