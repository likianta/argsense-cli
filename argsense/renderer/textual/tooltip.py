import typing as t

from textual.widgets import Label
from textual.widgets import Static

from .textual_sugar import log


class Help(Label):
    _info: str
    _tooltip: Static
    
    def __init__(self, info: str) -> None:
        super().__init__(':grey_question:' if info else '')
        # if not info:
        #     self.disabled = True
        #     return
        self.styles.width = 5
        self.styles.height = 3
        self.styles.content_align_vertical = 'middle'
        self.styles.text_align = 'left'
        self._info = info
    
    # def compose(self) -> ComposeResult:
    #     self.styles.content_align_vertical = 'middle'
    #     self.styles.text_align = 'center'
    #     self.update('[?]')
    #     with Tooltip(self._info) as tooltip:
    #         pass
    #     self._tooltip = tooltip
    #     yield tooltip
    
    def on_click(self) -> None:
        if self._info: log(self._info)
    
    def watch_mouse_over(self, value: bool) -> None:
        if not self._info: return
        # self.styles.background = 'yellow' if value else None
        self.update(':bulb:' if value else ':grey_question:')


class Tooltip(Static):  # TODO: not used
    
    def __init__(self, desc: str) -> None:
        super().__init__()
        w, h = self._get_best_size(desc)
        self.styles.layer = 'tooltip'
        self.styles.width = w
        self.styles.height = h
        self.styles.max_height = '50%'
        self.update(desc)
    
    @staticmethod
    def _get_best_size(desc: str) -> t.Tuple[int, int]:
        if not desc: return 0, 0
        lines = desc.splitlines()
        w = max(map(len, lines))
        h = len(lines)
        return w, h
