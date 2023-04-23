from textual import widgets as w
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget

from .typehint import T
from .typehint import t
from ...converter import cval_to_val
from ...parser import ParamType


class E:
    class Undefined: ...  # TODO: not used yet
    
    class UnfilledArgument(Exception): ...


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
                    form.styles.height = '100%'
        self.control = switcher
        yield switcher
    
    def get_exec(self) -> t.Callable:
        form: MainForm = self.query_one('#' + self.control.current)
        return form.get_exec()
    
    def run(self) -> t.Any:
        form: MainForm = self.query_one('#' + self.control.current)
        return form.exec()


class MainForm(Widget):
    control: Container
    
    def __init__(self, id: str, func_info: T.FuncInfo):
        super().__init__(id=id)
        self._func_info = func_info
    
    def compose(self) -> ComposeResult:
        with Container() as container:
            has_child = False
            
            for key, dict_ in self._func_info.args.items():
                if key.startswith('*'):
                    continue
                has_child = True
                with MainRow(
                        label=dict_['cname'],
                        param_name=key,
                        param_type='arg',
                        value_default='',
                        value_type=dict_['ctype'],
                ) as row:
                    row.styles.height = 3
            
            for key, dict_ in self._func_info.kwargs.items():
                if key.startswith((':', '*')):
                    continue
                has_child = True
                with MainRow(
                        label=dict_['cname'].lstrip('-'),
                        param_name=key,
                        param_type='opt',
                        value_default=str(dict_['default']),
                        value_type=dict_['ctype'],
                ) as row:
                    row.styles.height = 3
            
            if not has_child:
                # container.styles.content_align = 'center'
                with w.Static() as placeholder:
                    placeholder.styles.padding = (0, 1, 1, 2)
                    #   the same with `./app.py : var main_desc : padding`
                    placeholder.update(
                        '[dim]no parameter for this command. \n'
                        'you can click "run" button directly.[/]'
                    )
        
        self.control = container
        yield container
    
    def grab_data(self) -> dict:
        row: MainRow
        out = {}
        for row in self.control.children:
            if (value := row.value) is MainRow.Undefined:
                if row.row_type == 'arg':
                    raise E.UnfilledArgument('unfilled argument', row.key)
                else:
                    continue
            out[row.key] = value
        print(out, ':l')
        return out
    
    def get_exec(self) -> t.Callable:
        from functools import partial
        return partial(self._func_info.target, **self.grab_data())
    
    def exec(self) -> t.Any:
        from textual.app import active_app
        target = self._func_info.target
        params = self.grab_data()
        active_app.get().exit(0)
        return target(**params)


class MainRow(Widget):
    class Undefined:
        pass
    
    def __init__(
            self,
            label: str,
            param_name: str,
            param_type: t.Literal['arg', 'opt'],
            value_default: str,
            value_type: ParamType,
            help: str = '[?]',
    ) -> None:
        super().__init__()
        self.key = param_name
        self.label = label
        self.row_type = param_type
        self._default = value_default
        self._help = help
        self._input = None
        self._placeholder = value_type.name
        self._type = value_type
        if param_type == 'opt':
            self._placeholder += f'. default {self._default}'
    
    @property
    def kv(self) -> t.Tuple[str, t.Any]:
        return self.key, self.value
    
    @property
    def value(self) -> t.Union[t.Any, 'MainRow.Undefined']:
        if self._input.value:
            return cval_to_val(self._input.value, self._type)
        else:
            return MainRow.Undefined
    
    def compose(self) -> ComposeResult:
        with Container() as row:
            row.styles.width = '100%'
            row.styles.height = 3
            row.styles.layout = 'horizontal'
            
            with w.Static(self.label + ': ') as label:
                label.styles.width = 10
                label.styles.height = 3
                label.styles.align = ('right', 'middle')
                label.styles.content_align_vertical = 'middle'
                # label.styles.dock = 'left'
                label.styles.text_align = 'right'
                if self.row_type == 'opt':
                    label.styles.color = 'gray'
                    # label.styles.text_style = 'dim'
            
            with w.Input() as input_:
                input_.styles.width = '50%'
                input_.styles.height = '100%'
                input_.placeholder = self._placeholder
                input_.value = self._default
                self._input = input_
            
            with w.Static(self._help) as help:
                help.styles.width = 5
                help.styles.height = 3
                # help.styles.background = '#e15827'
                help.styles.content_align_vertical = 'middle'
                # help.styles.dock = 'right'
                help.styles.text_align = 'center'
        
        yield row
    
    def get_value(self) -> str:
        return self._input.value
