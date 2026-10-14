import io
import re
import typing as t
from contextlib import redirect_stdout

from rich.text import Text
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import RichLog
from textual.widgets import Static
from textual.widgets import Switch

from ...converter import args_2_cargs
from ...parser import Argv
from ...parser import FuncInfo
from ...parser import ParamType
from ...parser import parse_argv
from ...parser.args_parser import exceptions as e


class T:
    Row = t.Tuple[str, dict]
    #   (python param name, param info dict)


def collect_rows(func_info: FuncInfo) -> t.List[T.Row]:
    """
    Build the form rows: one row per parameter, in the order they are
    declared in the function signature.

    Variadic parameters (`*args` / `**kwargs`) are skipped, because a form
    cannot express "any number of values".
    """
    return [
        *func_info.args0.items(),
        *func_info.args1.items(),
        *func_info.args3.items(),
    ]


def widget_id(name: str) -> str:
    return 'param-{}'.format(name)


def _label(info: dict) -> str:
    # e.g. '--use-exist, -u' -> 'use-exist'
    return info['cname'].split(',')[0].strip().lstrip('-')


def _default_text(info: dict) -> str:
    value = info.get('default', ...)
    if value is ... or value is None or isinstance(value, bool):
        return ''
    return str(value)


def _plain(text: str) -> str:
    """
    Strip the rich markup that the cli-oriented error messages carry, so that
    they can be shown as-is in the tui.
    """
    return re.sub(r'\[/?[^\[\]]*\]', '', text)


class ArgsenseTuiApp(App[t.Any]):
    CSS = """
    #form {
        width: 100%;
        height: auto;
        padding: 0 2;
    }
    #desc {
        color: $text-muted;
        margin-bottom: 1;
    }
    .row {
        height: auto;
    }
    .row > .name {
        width: 18;
        padding: 1 1 0 0;
        text-align: right;
        color: $text-muted;
    }
    .row > Input {
        width: 1fr;
    }
    .row > Switch {
        width: auto;
    }
    #actions {
        height: auto;
        margin-top: 1;
    }
    #actions > Button {
        width: 50%;
    }
    #log {
        height: 5;
        margin-top: 1;
        border: round $primary;
        padding: 0 1;
    }
    """

    BINDINGS = [('escape', 'quit', 'Quit')]

    def __init__(self, func_info: FuncInfo) -> None:
        super().__init__()
        self.func_info = func_info
        self.rows = collect_rows(func_info)
        self.title = func_info.name
        self.sub_title = 'argsense'

    def compose(self) -> ComposeResult:
        with Vertical(id='form'):
            if self.func_info.desc:
                yield Static(self.func_info.desc, id='desc')
            for name, info in self.rows:
                with Horizontal(classes='row'):
                    yield Label(_label(info), classes='name')
                    if info['ctype'] is ParamType.FLAG:
                        yield Switch(
                            value=bool(info.get('default')), id=widget_id(name)
                        )
                    else:
                        yield Input(
                            value=_default_text(info),
                            placeholder=info['desc'],
                            id=widget_id(name),
                        )
            with Horizontal(id='actions'):
                yield Button('Run', id='run', variant='primary')
                yield Button('Run and exit', id='run-exit')
            yield RichLog(id='log', max_lines=1000, markup=False)

    def on_mount(self) -> None:
        self.query_one('#log', RichLog).border_title = 'log'

    # --------------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'run':
            self.execute(exit_on_success=False)
        elif event.button.id == 'run-exit':
            self.execute(exit_on_success=True)

    def execute(self, exit_on_success: bool) -> None:
        try:
            args, kwargs = self.parse_form()
        except e.ArgvParsingFailed as exc:
            self.write_log(Text(_plain(str(exc)), style='red'))
            return

        # everything the target function prints is collected and shown in the
        # log panel, rather than being mixed into the tui rendering.
        capture = io.StringIO()
        try:
            with redirect_stdout(capture):
                result = self.func_info.target(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            self.flush_capture(capture)
            self.write_log(
                Text('{}: {}'.format(type(exc).__name__, exc), style='red')
            )
            return

        self.flush_capture(capture)
        if result is None:
            self.write_log(Text('done', style='green'))
        else:
            self.write_log(Text('done -> {!r}'.format(result), style='green'))

        if exit_on_success:
            self.exit(result)

    def write_log(self, content: t.Any) -> None:
        # note: don't name this `log` - `App.log` is textual's own logger.
        self.query_one('#log', RichLog).write(content)

    def flush_capture(self, capture: io.StringIO) -> None:
        text = capture.getvalue()
        if text.strip():
            self.write_log(Text(text.rstrip('\n')))

    def parse_form(self) -> t.Tuple[t.Sequence[t.Any], t.Dict[str, t.Any]]:
        """
        Turn the form into `(args, kwargs)`, by rebuilding a command line and
        feeding it to the very same parser that the cli interface uses. This
        keeps type conversion, default values and error messages identical.
        """
        tokens: t.List[str] = []
        for name, _info in self.rows:
            widget = self.query_one('#{}'.format(widget_id(name)))
            if isinstance(widget, Switch):
                tokens += args_2_cargs(**{name: widget.value})
            elif isinstance(widget, Input):
                text = widget.value.strip()
                if text:
                    tokens += args_2_cargs(**{name: text})

        result = parse_argv(
            Argv(('argsense',), ('tui',), tuple(tokens)),
            mode='command',
            front_matter={
                'args': {k: v['ctype'] for k, v in self.func_info.args.items()},
                'kwargs': {
                    k: v['ctype']
                    for k, v in self.func_info.extended_kwargs.items()
                },
                'index': self.func_info.cname_2_name,
            },
            implicit_help=False,
            raise_on_error=True,
        )
        assert result is not None
        return tuple(result['args'].values()), result['kwargs']


def run_form(func_info: FuncInfo, inline: bool = False) -> t.Any:
    """
    Launch the form and return the target function's return value.
    """
    return ArgsenseTuiApp(func_info).run(inline=inline)
