"""
The three-state switch for an `Optional[bool]` parameter.
"""

import typing as t

from rich.console import RenderableType
from textual.binding import Binding
from textual.binding import BindingType
from textual.events import Click
from textual.geometry import Size
from textual.message import Message
from textual.reactive import reactive
from textual.scrollbar import ScrollBarRender
from textual.widget import Widget


class TripleSwitch(Widget, can_focus=True):
    """
    A switch whose knob rests on one of three positions: `False` on the left,
    `None` in the middle and `True` on the right.

    It is the widget of a `bool | None` parameter (see `is_triple_switch` in
    `app.py`). On the command line such a parameter is a flag, and a flag can
    only spell its two boolean states (`--xxx` / `--no-xxx`) - the third one
    has no command line spelling, so the form gives it a widget of its own.

    Click a third of the switch to pick the state of that third, or press
    enter / space to slide the knob one position to the right (wrapping).

    The knob is highlighted by the class of the state it rests on: `-off`
    (red, `False`), `-none` (yellow, `None`) and `-on` (green, `True`).

    This is a trimmed down `textual.widgets.Switch`: the same slider, drawn
    with `ScrollBarRender`, which is what turns a progress bar into a "knob"
    (the bar is drawn reversed, and the window takes a third of it). Only the
    value is tri-state instead of boolean, so the knob has three positions.
    """

    BINDINGS: t.ClassVar[t.List[BindingType]] = [
        Binding('enter,space', 'cycle', 'Cycle', show=False)
    ]

    COMPONENT_CLASSES: t.ClassVar[t.Set[str]] = {'triple-switch--slider'}

    ALLOW_SELECT = False

    DEFAULT_CSS = """
    TripleSwitch {
        border: tall $border-blurred;
        background: $surface;
        height: auto;
        width: auto;
        pointer: pointer;
        padding: 0 2;

        & .triple-switch--slider {
            color: $panel;
            background: $panel-darken-2;
        }
        &.-off .triple-switch--slider {
            color: $error;
        }
        &.-none .triple-switch--slider {
            color: $warning;
        }
        &.-on .triple-switch--slider {
            color: $success;
        }
        &:hover {
            &.-off > .triple-switch--slider {
                color: $error-lighten-1;
            }
            &.-none > .triple-switch--slider {
                color: $warning-lighten-1;
            }
            &.-on > .triple-switch--slider {
                color: $success-lighten-1;
            }
        }
        &:focus {
            border: tall $border;
            background-tint: $foreground 5%;
        }
    }
    """

    STATES: t.ClassVar[t.Tuple[t.Optional[bool], ...]] = (False, None, True)
    #   the resting positions of the knob, from left to right.

    CONTENT_WIDTH = 2 * len(STATES)
    #   two cells per position, so that the knob (a third of the bar) rests on
    #   a position of its own; it also keeps the ratio that `render` asks
    #   `ScrollBarRender` for.

    value = reactive[t.Optional[bool]](None, init=False)
    #   one of the `STATES`.

    _slider_position = reactive(0.0)
    #   where the knob sits, in state units: 0.0 is `False`, 1.0 is `None` and
    #   2.0 is `True`. It is a float, and it - rather than `value` - is what
    #   `render` draws, so that a change of `value` can slide the knob to its
    #   new position (see `watch_value`).

    class Changed(Message):
        """Posted when the state of the switch changes.

        Attributes:
            value: The state that the switch was changed to.
            switch: The `TripleSwitch` widget that was changed.
        """

        def __init__(
            self, switch: 'TripleSwitch', value: t.Optional[bool]
        ) -> None:
            super().__init__()
            self.value = value
            self.switch = switch

        @property
        def control(self) -> 'TripleSwitch':
            """Alias for self.switch."""
            return self.switch

    def __init__(
        self,
        value: t.Optional[bool] = None,
        *,
        animate: bool = True,
        name: t.Optional[str] = None,
        id: t.Optional[str] = None,
        classes: t.Optional[str] = None,
        disabled: bool = False,
        tooltip: t.Optional[RenderableType] = None,
    ) -> None:
        """Initialise the switch, with `None` as its initial state."""
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._should_animate = animate
        # `set_reactive` skips the watcher, so a widget that is not on screen
        # yet posts no `Changed` - its state class is set by hand instead.
        self.set_reactive(TripleSwitch.value, value)
        self._apply_state_class(value)
        self._slider_position = float(self.STATES.index(value))
        if tooltip is not None:
            self.tooltip = tooltip

    def watch_value(self, value: t.Optional[bool]) -> None:
        self._apply_state_class(value)
        target_position = float(self.STATES.index(value))
        if self._should_animate:
            self.animate(
                '_slider_position', target_position, duration=0.3, level='basic'
            )
        else:
            self._slider_position = target_position
        self.post_message(self.Changed(self, value))

    def render(self) -> RenderableType:
        style = self.get_component_rich_style('triple-switch--slider')
        return ScrollBarRender(
            virtual_size=100 * len(self.STATES),
            window_size=100,
            position=100 * self._slider_position,
            style=style,
            vertical=False,
        )

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return self.CONTENT_WIDTH

    def get_content_height(
        self, container: Size, viewport: Size, width: int
    ) -> int:
        return 1

    async def _on_click(self, event: Click) -> None:
        """Pick the state of the third that was clicked."""
        event.stop()
        region = self.content_region
        if not region.width:
            return
        index = (event.screen_x - region.x) * len(self.STATES) // region.width
        self.value = self.STATES[min(max(index, 0), len(self.STATES) - 1)]

    def action_cycle(self) -> None:
        """Slide the knob to the next position."""
        index = self.STATES.index(self.value)
        self.value = self.STATES[(index + 1) % len(self.STATES)]

    def _apply_state_class(self, value: t.Optional[bool]) -> None:
        # the state names its own highlight color (see `DEFAULT_CSS`).
        self.set_class(value is False, '-off')
        self.set_class(value is None, '-none')
        self.set_class(value is True, '-on')
