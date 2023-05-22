from rich.console import RenderableType
from textual.widgets import Static


class MainDesc(Static):
    
    def __init__(self, desc: str) -> None:
        super().__init__(desc or '[dim]no description.[/]')
        self.styles.width = '100%'
        self.styles.height = 'auto'
        self.styles.max_height = 5
    
    def update(self, desc: RenderableType = '') -> None:
        super().update(desc or '[dim]no description.[/]')
