from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button

from .signal_slot import Signal


class BottomBar(Container):
    run_triggered = Signal()
    
    # def __init__(self, target: t.Callable):
    #     super().__init__()
    #     self._target = target
    
    def compose(self) -> ComposeResult:
        self.styles.width = '100%'
        self.styles.height = 3
        
        with Container() as bar:
            bar.styles.layout = 'horizontal'
            
            with Button('Run', id='run') as btn:
                btn.styles.width = 'auto'
                btn.styles.padding = 0
        
        yield bar
    
    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == 'run':
            self.run_triggered.emit()
