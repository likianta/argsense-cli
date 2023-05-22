from textual import widgets as w
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget

from .tooltip import Help
from .typehint import T
from .typehint import t
from ...converter import str_2_val
from ...converter import val_2_str
from ...parser import ParamType


class E:
    class Undefined: ...  # TODO: not used yet. see also `MainRow.Undefined`
    
    class UnfilledArgument(Exception): ...


def _get_proper_width(text_list: t.Sequence[str], limit: int = 0) -> int:
    max_ = max(map(len, text_list))
    if limit and max_ > limit:
        return limit
    return max_


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
            label_width = _get_proper_width(
                (*self._func_info.args.keys(),
                 *self._func_info.kwargs.keys()),
                limit=20
            ) + 1
            
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
                        help=dict_['desc'],
                        label_width=label_width,
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
                        value_default=dict_['default'],
                        value_type=dict_['ctype'],
                        help=dict_['desc'],
                        label_width=label_width,
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
            value_default: t.Any,
            value_type: ParamType,
            help: str,
            **kwargs
    ) -> None:
        super().__init__()
        self.key = param_name
        self.label = label
        self.row_type = param_type
        self._default = value_default
        self._help = help
        self._input = None
        self._label_width = kwargs.get('label_width', 10)
        self._placeholder = value_type.name
        self._reqmark: t.Optional[w.Static] = None
        self._type = value_type
        if param_type == 'opt':
            self._placeholder += '. default {}'.format(
                val_2_str(self._default, self._type)
            )
    
    @property
    def kv(self) -> t.Tuple[str, t.Any]:
        return self.key, self.value
    
    @property
    def value(self) -> t.Union[t.Any, 'MainRow.Undefined']:
        if self._input.value:
            return self._eval_input_value(self._input.value, self._type)
        elif self.row_type == 'opt':
            return self._default
        else:
            return MainRow.Undefined
        
    def _eval_input_value(self, value: str, type_: ParamType) -> t.Any:
        if type_ != ParamType.TEXT and not value.strip():
            return self._default
        return str_2_val(value, type_)
    
    def compose(self) -> ComposeResult:
        with Container() as row:
            row.styles.width = '100%'
            row.styles.height = 3
            row.styles.layout = 'horizontal'
            
            with w.Static(self.label + ': ', shrink=True) as label:
                label.styles.width = self._label_width
                label.styles.height = 1
                label.styles.align = ('right', 'middle')
                label.styles.content_align_vertical = 'middle'
                label.styles.margin = (1, 0)
                # label.styles.dock = 'left'
                label.styles.text_align = 'right'
                if self.row_type == 'opt':
                    label.styles.color = 'gray'
                    # label.styles.text_style = 'dim'
                if len(self.label) > self._label_width:
                    label.update('{}{}{}{}'.format(
                        self.label[:self._label_width - 3],
                        '[#7C7777]{}[/]'.format(
                            self.label[self._label_width - 3]
                        ),
                        '[#5E5D5D]{}[/]'.format(
                            self.label[self._label_width - 2]
                        ),
                        '[#3B3939]{}[/]'.format(
                            self.label[self._label_width - 1]
                        ),
                    ))
            
            with w.Input() as input_:
                input_.styles.width = '50%'
                input_.styles.height = '100%'
                # input_.styles.border = ('round', '#406FCE')
                input_.placeholder = self._placeholder
                input_.value = val_2_str(self._default, self._type)
            self._input = input_
            
            with w.Static() as reqmark:
                reqmark.styles.width = 1
                reqmark.styles.height = 1
                if self.row_type == 'arg':
                    reqmark.update('*')
                    reqmark.styles.color = 'red'
                    self._reqmark = reqmark
                # else: it is a placeholder with nothing to do
            
            yield Help(self._help)
        
        yield row
    
    def on_input_changed(self, e: w.Input.Changed) -> None:
        if self._reqmark:
            self._reqmark.styles.color = 'grey' if e.value else 'red'
    
    def get_value(self) -> str:
        return self._input.value
