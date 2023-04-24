from typing import cast

from rich.text import Text
from rich.text import TextType
from textual import events
from textual import widgets as w
from textual.containers import Container as BaseContainer
from textual.reactive import reactive
from textual.widget import Widget as BaseWidget

from .signal import Signal
from .signal import SignalInit


class Container(BaseContainer, SignalInit):
    pass


class Widget(BaseWidget, SignalInit):
    pass


class FlatButton(w.Static, SignalInit):
    clicked = Signal()
    label = cast(str, reactive(''))
    
    # class Pressed(Message, bubble=True):
    #     def __init__(self, button: 'FlatButton') -> None:
    #         self.control = button
    #         super().__init__()
    
    def __init__(
            self,
            label: TextType | None = None,
            *,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.label = label
    
    def render(self) -> TextType:
        label = Text.assemble(" ", self.label, " ")
        label.stylize(self.text_style)
        return label
    
    async def _on_click(self, e: events.Click) -> None:
        e.stop()
        if self.display and not self.disabled:
            self.clicked()


class Button(w.Button, SignalInit):
    clicked = Signal()
    
    def on_button_pressed(self):
        self.clicked.emit()
