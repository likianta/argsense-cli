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
from ...converter import val_2_cval
from ...parser import Argv
from ...parser import FuncInfo
from ...parser import ParamType
from ...parser import parse_argv
from ...parser.args_parser import exceptions as e


class T:
    Row = t.Tuple[str, dict]
    #   (python param name, param info dict)
    InitialValues = t.Dict[str, t.Any]


class CliRunRequest:
    """
    The value the form returns when the user pressed "Run and exit".

    By then the tui has already closed, so the caller is expected to rebuild the
    command line from `tokens` and run it through the cli path. That way the
    target function's prints land on the real console, instead of being captured
    by the (now gone) log panel.
    """

    def __init__(self, tokens: t.Tuple[str, ...]) -> None:
        self.tokens = tokens


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


def front_matter(func_info: FuncInfo) -> dict:
    """
    The same `front_matter` that the cli interface hands to the parser.
    """
    return {
        'args': {k: v['ctype'] for k, v in func_info.args.items()},
        'kwargs': {k: v['ctype'] for k, v in func_info.extended_kwargs.items()},
        'index': func_info.cname_2_name,
    }


def collect_initial_values(func_info: FuncInfo, argv: Argv) -> T.InitialValues:
    """
    Best effort: map a command line onto form values, so that
    `python main.py Alice 22` opens the form with 'Alice' and '22' filled in.

    Only the parameters the user actually gave are returned, and a command
    line that does not parse at all simply yields nothing.
    """
    try:
        result = parse_argv(
            argv,
            mode='command',
            front_matter=front_matter(func_info),  # type: ignore
            implicit_help=False,
            raise_on_error=True,
        )
    except e.ArgvParsingFailed:
        return {}

    assert result is not None
    infos = {**func_info.args, **func_info.kwargs}
    values: T.InitialValues = {}
    for name, value in {**result['args'], **result['kwargs']}.items():
        info = infos.get(name)
        if info is None:
            continue
        if value == info.get('default', ...):
            # not given by the user; the form shows the default anyway.
            continue
        values[name] = value if isinstance(value, bool) else val_2_cval(value)
    return values


def _label(info: dict) -> str:
    # e.g. '--use-exist, -u' -> 'use-exist'
    return info['cname'].split(',')[0].strip().lstrip('-')


def _default_text(info: dict) -> str:
    value = info.get('default', ...)
    if value is ... or value is None or isinstance(value, bool):
        return ''
    return str(value)


def _default_flag(info: dict) -> bool:
    return bool(info.get('default'))


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
        height: 100%;
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
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    #run {
        width: 1fr;
    }
    #run-exit {
        width: 1fr;
        margin-left: 1;
    }
    #exit {
        width: auto;
        margin-left: 1;
    }
    #log {
        height: 1fr;
        margin-top: 1;
        border: round $primary;
        padding: 0 1;
    }
    """

    BINDINGS = [('escape', 'quit', 'Quit')]

    def __init__(
        self,
        func_info: FuncInfo,
        inline: bool = False,
        initial: t.Optional[T.InitialValues] = None,
    ) -> None:
        super().__init__()
        self.func_info = func_info
        self.rows = collect_rows(func_info)
        self.inline = inline
        self.initial: T.InitialValues = initial or {}
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
                            value=bool(
                                self.initial.get(name, _default_flag(info))
                            ),
                            id=widget_id(name),
                        )
                    else:
                        yield Input(
                            value=str(
                                self.initial.get(name, _default_text(info))
                            ),
                            placeholder=info['desc'],
                            id=widget_id(name),
                        )
            with Horizontal(id='actions'):
                yield Button('Run', id='run', variant='primary')
                yield Button('Run and exit', id='run-exit')
                yield Button('Exit', id='exit', variant='error')
            yield RichLog(id='log', max_lines=1000, markup=False)

    def on_mount(self) -> None:
        self.query_one('#log', RichLog).border_title = 'log'
        if self.inline:
            # inline mode: the form is a fixed-height block, so the log panel
            # gets 5 lines of content (plus the two border rows).
            self.query_one('#form').styles.height = 'auto'
            self.query_one('#log', RichLog).styles.height = 7

    # --------------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'run':
            self.execute()
        elif event.button.id == 'run-exit':
            # hand the assembled command line back to the caller, which runs it
            # through the cli path once the tui has closed - so that the target
            # function's prints are not swallowed by the log panel.
            self.exit(CliRunRequest(tuple(self.collect_tokens())))
        elif event.button.id == 'exit':
            self.exit()

    def execute(self) -> None:
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

    def write_log(self, content: t.Any) -> None:
        # note: don't name this `log` - `App.log` is textual's own logger.
        self.query_one('#log', RichLog).write(content)

    def flush_capture(self, capture: io.StringIO) -> None:
        text = capture.getvalue()
        if text.strip():
            self.write_log(Text(text.rstrip('\n')))

    def collect_tokens(self) -> t.List[str]:
        """
        Assemble the command line tokens from the current form values.
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
        return tokens

    def parse_form(self) -> t.Tuple[t.Sequence[t.Any], t.Dict[str, t.Any]]:
        """
        Turn the form into `(args, kwargs)`, by rebuilding a command line and
        feeding it to the very same parser that the cli interface uses. This
        keeps type conversion, default values and error messages identical.
        """
        result = parse_argv(
            Argv(('argsense',), ('tui',), tuple(self.collect_tokens())),
            mode='command',
            front_matter=front_matter(self.func_info),  # type: ignore
            implicit_help=False,
            raise_on_error=True,
        )
        assert result is not None
        return tuple(result['args'].values()), result['kwargs']


def run_form(
    func_info: FuncInfo,
    inline: bool = False,
    argv: t.Optional[Argv] = None,
    cli_runner: t.Optional[t.Callable[[t.Tuple[str, ...]], t.Any]] = None,
) -> t.Any:
    """
    Launch the form and return the target function's return value.

    params:
        argv:
            an optional command line, whose values prefill the form.
        cli_runner:
            called with the assembled tokens when the user pressed "Run and
            exit". It should run the command line through the cli path.
    """
    initial = collect_initial_values(func_info, argv) if argv else {}
    app = ArgsenseTuiApp(func_info, inline=inline, initial=initial)
    result = app.run(inline=inline)
    if isinstance(result, CliRunRequest) and cli_runner is not None:
        return cli_runner(result.tokens)
    return result
