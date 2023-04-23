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
    
    def __init__(self, funcs_info: T.FuncsInfo) -> None:
        super().__init__()
        self._funcs_info = funcs_info
    
    def compose(self) -> ComposeResult:
        with Container() as root:
            with Sidebar(
                    (x['cname'] for x in self._funcs_info)
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
