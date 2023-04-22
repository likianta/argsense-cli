from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button

from .textual_sugar import Signal
from .textual_sugar import Widget


class BottomBar(Widget):
    run_triggered = Signal()
    
    def compose(self) -> ComposeResult:
        with Container() as bar:
            bar.styles.height = 3
            bar.styles.layout = 'horizontal'
            
            with Button('Run', id='run') as btn:
                btn.styles.width = 'auto'
                btn.styles.padding = 0
        
        yield bar
    
    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == 'run':
            self.run_triggered.emit()
