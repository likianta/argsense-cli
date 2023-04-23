import typing as t

from textual import widgets as w
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import Vertical
from textual.screen import Screen

from .bottom_bar import BottomBar
from .main_form import E
from .main_form import MainFormContainer
from .sidebar import Sidebar
from .textual_sugar import FlatButton
from .textual_sugar import add_post_exec
from .textual_sugar import bind_signal
from .textual_sugar import post_exec
from .typehint import T


def run(funcs_info: T.FuncsInfo) -> t.Any:
    app = MyApp(funcs_info)
    app.run()
    return post_exec()


class MyApp(App):
    
    def __init__(self, funcs_info: T.FuncsInfo) -> None:
        super().__init__()
        self._funcs_info = funcs_info
    
    def compose(self) -> ComposeResult:
        with Screen() as scr:
            scr.styles.layers = ('main', 'full_log')
        
        with Container() as root:
            root.styles.layer = 'main'
            
            with Sidebar(
                    (x.name for x in self._funcs_info)
            ) as sidebar:
                sidebar.styles.width = 20
                sidebar.styles.dock = 'left'
                
                @bind_signal(sidebar.clicked)
                def _(idx: int, item: FlatButton):
                    print(f'sidebar item ({idx}) clicked', item.label)
                    log.write(f'sidebar item ({idx}) clicked: {item.label}')
                    main_form.control.current = f'form-{idx}'
            
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
                            try:
                                # activate_full_log()
                                # main_form.run()
                                add_post_exec(main_form.get_exec())
                                self.exit()
                            except E.UnfilledArgument as e:
                                log.write(str(e))
                    
                    with w.TextLog() as log:
                        log.styles.width = '100%'
                        log.styles.height = 10
                        # log.styles.dock = 'bottom'
                        log.styles.background = '#282C34'
                        log.styles.border = ('round', '#FEA62B')
        
        with w.TextLog() as full_log:
            full_log.styles.layer = 'full_log'
            full_log.styles.width = '100%'
            full_log.styles.height = 0
            full_log.styles.dock = 'bottom'
            
            def activate_full_log() -> w.TextLog:  # TODO
                full_log.styles.height = '100%'
                # full_log.animate('height', 20)
                return full_log
        
        yield root
