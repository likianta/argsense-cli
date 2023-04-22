from textual import widgets as w
from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical

from .bottom_bar import BottomBar
from .main_form import MainFormContainer
from .sidebar import Sidebar
from .textual_sugar import FlatButton
from .textual_sugar import bind_signal
from .typehint import T


def run(funcs_info: T.FuncsInfo) -> None:
    app = MyApp(funcs_info)
    app.run()


class MyApp(App):
    BINDINGS = [
        ('d', 'toggle_dark', 'Toggle dark mode'),
        Binding('ctrl+c,ctrl+q', 'app.quit', 'Quit', show=True),
    ]
    
    # # for textual dev test
    # # window 1: textual console -x EVENT
    # # window 2: textual run --dev argsense/tui/app.py
    # def __init__(self, **__) -> None:
    #     super().__init__()
    #     self._target = lambda *args, **kwargs: print(args, kwargs)
    #     self._params = {
    #         'name'  : str,
    #         'age'   : int,
    #         'gender': str,
    #     }
    
    def __init__(self, funcs_info: T.FuncsInfo) -> None:
        super().__init__()
        self._funcs_info = funcs_info
    
    def compose(self) -> ComposeResult:
        with Container() as root:
            with Sidebar(
                    ('alpha', 'beta', 'gamma')
            ) as sidebar:
                sidebar.styles.width = 20
                sidebar.styles.dock = 'left'
                
                @bind_signal(sidebar.clicked)
                def _(idx: int, item: FlatButton):
                    print(f'sidebar item ({idx}) clicked', item.label)
                    log.write(f'sidebar item ({idx}) clicked: {item.label}')
                    main_form.control.current = f'form-{idx}'
                
                # for n in names:
                #     yield LocationLink(n, f'.location-{n}')
            
            with Container() as main_zone:
                main_zone.styles.width = '100%'
                main_zone.styles.height = '100%'
                main_zone.styles.align = ('center', 'middle')
                main_zone.styles.padding = (1, 1, 0, 1)
                # main_zone.styles.background = '#5ac2dc'
                # main_zone.styles.color = 'black'
                
                with w.Static('Description zone for AAA') as desc_zone:
                    desc_zone.styles.width = '100%'
                    desc_zone.styles.height = 3
                    desc_zone.styles.align = ('center', 'middle')
                
                with MainFormContainer(self._funcs_info) as main_form:
                    main_form.styles.width = '100%'
                    main_form.styles.height = 'auto'
                
                with Vertical() as vbox:
                    vbox.styles.height = 'auto'
                    vbox.styles.dock = 'bottom'
                
                    with BottomBar() as bbar:
                        bbar.styles.height = 3
                        # bbar.styles.dock = 'bottom'
                        
                        @bind_signal(bbar.run_triggered)
                        def _() -> None:
                            main_form.run()
                    
                    with w.TextLog() as log:
                        log.styles.width = '100%'
                        log.styles.height = 10
                        # log.styles.dock = 'bottom'
                        log.styles.background = '#282C34'
                        log.styles.border = ('round', '#FEA62B')
        
        yield root
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark  # noqa


class LocationLink(w.Static):
    
    def __init__(self, label: str, reveal: str) -> None:
        super().__init__(label)
        self.reveal = reveal
    
    def on_click(self) -> None:
        self.app.query_one(self.reveal).scroll_visible(top=True, duration=0.5)


if __name__ == "__main__":
    # py argsense/render/textual/app.py
    
    def _just_print(*args, **kwargs) -> None:
        print(args, kwargs)
    
    
    app = MyApp(
        (
            {
                'name'  : 'just-print',
                'func'  : _just_print,
                'params': {
                    'name'  : str,
                    'age'   : int,
                    'gender': str,
                }
            },
        )
    )
    app.run()
