from textual.app import App
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Static, Input


class MyApp(App):
    CSS_PATH = 'app.css'
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode")
    ]
    
    def compose(self) -> ComposeResult:
        names = ('aaa', 'bbb', 'ccc')
        params = {
            'mmm': bool,
            'nnn': int,
            'ooo': str,
        }
        
        with Container():
            with Container(id='sidebar'):
                yield Static('sidebar')
                for n in names:
                    yield LocationLink(n, f'.location-{n}')
            
            with Container() as main_zone:
                main_zone.styles.align = ('center', 'middle')
                # main_zone.styles.background = '#5ac2dc'
                # main_zone.styles.color = 'black'
                main_zone.styles.height = '100%'
                main_zone.styles.padding = (1, 1, 0, 1)
                main_zone.styles.width = '100%'
                
                yield Static('description zone for AAA')
                with Container(id='main-form'):
                    for k, v in params.items():
                        yield Static(k)
                        yield Input(placeholder=f'type: {v.__name__}')
                        yield Static('help')

                # with Container() as log_panel:
                #     log_panel.styles.background = '#25292d'
                #     log_panel.styles.dock = 'bottom'
                #     log_panel.styles.height = 1

                with Container() as bottom_bar:
                    bottom_bar.styles.background = '#d3544e'
                    bottom_bar.styles.dock = 'bottom'
                    bottom_bar.styles.height = 3
                    bottom_bar.styles.layout = 'horizontal'
                    
                    with Static('(command_prompt)') as cmd:
                        cmd.styles.width = 'auto'
                    # yield Static('(command_prompt)')
                    
                    with Button('copy') as btn:
                        btn.styles.width = 'auto'
                        btn.styles.padding = 0
                        
                    with Button('run') as btn:
                        btn.styles.width = 'auto'
                        btn.styles.padding = 0
                    
                    # class MyButton(Button):
                    #     def compose(self) -> ComposeResult:
                    #         yield super().compose()
                    #         self.styles.height = 1
                    #
                    # yield MyButton('copy')
                    # yield MyButton('run')
                
        yield Footer()
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark  # noqa


class LocationLink(Static):
    
    def __init__(self, label: str, reveal: str) -> None:
        super().__init__(label)
        self.reveal = reveal
    
    def on_click(self) -> None:
        self.app.query_one(self.reveal).scroll_visible(top=True, duration=0.5)


if __name__ == "__main__":
    app = MyApp()
    app.run()
