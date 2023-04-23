from textual import widgets as w
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Input
from textual.widgets import Static

from .typehint import T
from .typehint import t


class MainFormContainer(Widget):
    control: w.ContentSwitcher
    
    def __init__(self, funcs_info: T.FuncsInfo):
        super().__init__()
        # self._funcs_info = tuple(funcs_info)
        self._funcs_info = funcs_info
    
    def compose(self) -> ComposeResult:
        with w.ContentSwitcher(initial='form-0') as switcher:
            # switcher.styles.width = '100%'
            # switcher.styles.height = '100%'
            info: T.FuncInfo
            for i, info in enumerate(self._funcs_info):
                with MainForm(f'form-{i}', info) as form:
                    form.styles.width = '100%'
                    form.styles.height = 'auto'
        
        self.control = switcher
        yield switcher
    
    def run(self) -> t.Any:
        form: MainForm = self.query_one('#' + self.control.current)
        return form.exec()


class MainForm(Widget):
    _control: Container
    
    def __init__(self, id: str, func_info: T.FuncInfo):
        super().__init__(id=id)
        self._func_info = func_info
    
    def compose(self) -> ComposeResult:
        with Container() as container:
            for key, dict_ in self._func_info['args'].items():
                with MainRow(
                        key=key,
                        label=dict_['cname'],
                        placeholder=dict_['ctype'].name,
                ) as row:
                    row.styles.height = 3
            for key, dict_ in self._func_info['kwargs'].items():
                with MainRow(
                        key=key,
                        label=dict_['cname'],
                        placeholder=dict_['ctype'].name,
                        value=str(dict_['default']),
                ) as row:
                    row.styles.height = 3
        self._control = container
        yield container
    
    def grab_data(self) -> dict:
        return dict((x.kv for x in self._control.children))
        # return dict((x.kv for x in self.children[0].children))
    
    def exec(self) -> t.Any:
        return self._func_info['func'](**self.grab_data())


class MainRow(Widget):
    
    def __init__(
            self,
            key: str,
            label: str,
            placeholder: str,
            value: str = '',
            help: str = '[?]'
    ) -> None:
        super().__init__()
        self.key = key
        self.label = label
        self._placeholder = placeholder
        self._default = value
        self._help = help
        self._input = None
    
    @property
    def kv(self) -> t.Tuple[str, str]:
        return self.key, self._input.value
    
    def compose(self) -> ComposeResult:
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
            
            with Input() as input_:
                input_.styles.width = '50%'
                input_.styles.height = '100%'
                input_.placeholder = self._placeholder
                input_.value = self._default
                self._input = input_
            
            with Static(self._help) as help:
                help.styles.width = 5
                help.styles.height = 3
                # help.styles.background = '#e15827'
                help.styles.content_align_vertical = 'middle'
                # help.styles.dock = 'right'
                help.styles.text_align = 'center'
        
        yield row
    
    def get_value(self) -> str:
        return self._input.value
