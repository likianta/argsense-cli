from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Input
from textual.widgets import Static


class MainRow(Container):
    
    def __init__(self, label: str, placeholder: str, help_: str) -> None:
        super().__init__()
        self.label = label
        self.placeholder = placeholder
        self.help = help_
        self._input = None
    
    def compose(self) -> ComposeResult:
        self.styles.width = '100%'
        self.styles.height = 3
        # self.styles.layout = 'horizontal'
        # self.styles.padding = (0, 1)
        
        with Container() as row:
            row.styles.width = '100%'
            row.styles.height = 3
            row.styles.layout = 'horizontal'
            
            with Static(self.label + ': ') as label:
                label.styles.width = 10
                label.styles.height = 3
                label.styles.align = ('right', 'middle')
                label.styles.content_align_vertical = 'middle'
                # label.styles.dock = 'left'
                label.styles.text_align = 'right'
            
            with Input(placeholder=self.placeholder) as input_:
                input_.styles.width = '50%'
                input_.styles.height = '100%'
                self._input = input_
            
            with Static(self.help) as help_:
                help_.styles.width = 5
                help_.styles.height = 3
                # help_.styles.background = '#e15827'
                help_.styles.content_align_vertical = 'middle'
                # help_.styles.dock = 'right'
                help_.styles.text_align = 'center'
        
        yield row
        
    def get_value(self) -> str:
        return self._input.value
