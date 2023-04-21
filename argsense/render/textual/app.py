from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static

from .bottom_bar import BottomBar
from .main_form import MainRow


def run() -> None:
    app = MyApp()
    app.run()


class MyApp(App):
    BINDINGS = [
        ('d', 'toggle_dark', 'Toggle dark mode'),
        Binding('ctrl+c,ctrl+q', 'app.quit', 'Quit', show=True),
    ]
    
    # for textual dev test
    # window 1: textual console -x EVENT
    # window 2: textual run --dev argsense/tui/app.py
    def __init__(self, **__) -> None:
        super().__init__()
        self._target = lambda *args, **kwargs: print(args, kwargs)
        self._params = {
            'name'  : str,
            'age'   : int,
            'gender': str,
        }
    
    # def __init__(self, target: t.Callable, params_info: dict) -> None:
    #     super().__init__()
    #     self._target = target
    #     self._params = params_info
    
    def compose(self) -> ComposeResult:
        names = ('Alpha', 'Beta', 'Gamma')
        params = self._params
        
        with Container():
            
            with Container() as sidebar:
                sidebar.styles.width = 20
                sidebar.styles.padding = (1, 2)
                sidebar.styles.background = '#141a20'
                sidebar.styles.dock = 'left'
                
                for n in names:
                    yield LocationLink(n, f'.location-{n}')
            
            with Container() as main_zone:
                main_zone.styles.width = '100%'
                main_zone.styles.height = '100%'
                main_zone.styles.align = ('center', 'middle')
                main_zone.styles.padding = (1, 1, 0, 1)
                # main_zone.styles.background = '#5ac2dc'
                # main_zone.styles.color = 'black'
                
                with Static('Description zone for AAA') as desc_zone:
                    desc_zone.styles.width = '100%'
                    desc_zone.styles.height = 3
                    desc_zone.styles.align = ('center', 'middle')
                
                with Container() as main_form:
                    main_form.styles.width = '100%'
                    main_form.styles.height = 'auto'
                    # main_form.styles.align = ('center', 'middle')
                    main_form.styles.layout = 'vertical'
                    
                    rows = []
                    for k, v in params.items():
                        with MainRow(
                                k.title(), f'type: {v.__name__}', '[?]'
                        ) as row:
                            rows.append(row)
                
                with BottomBar() as bbar:
                    bbar.styles.dock = 'bottom'
                    bbar.run_triggered.connect(lambda: self._target({
                        k: v.get_value() for k, v in zip(
                            params.keys(), rows
                        )
                    }))
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark  # noqa
    
    # def action_toggle_quit(self) -> None:
    #     self.exit()


class LocationLink(Static):
    
    def __init__(self, label: str, reveal: str) -> None:
        super().__init__(label)
        self.reveal = reveal
    
    def on_click(self) -> None:
        self.app.query_one(self.reveal).scroll_visible(top=True, duration=0.5)


if __name__ == "__main__":
    # py argsense/tui/app.py
    app = MyApp(
        target=lambda *args, **kwargs: print(args, kwargs),
        params_info={
            'name'  : str,
            'age'   : int,
            'gender': str,
        }
    )
    app.run()
