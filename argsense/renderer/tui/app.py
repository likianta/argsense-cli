import io
import re
import typing as t
from contextlib import redirect_stdout

from rich.text import Text
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.containers import VerticalScroll
from textual.widgets import Button
from textual.widgets import ContentSwitcher
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import RichLog
from textual.widgets import Static
from textual.widgets import Switch
from textual.widgets import Tab
from textual.widgets import Tabs

from ...converter import args_2_cargs
from ...parser import Argv
from ...parser import FuncInfo
from ...parser import ParamType
from ...parser import parse_argv
from ...parser.args_parser import exceptions as e


class T:
    Row = t.Tuple[str, dict]
    #   (python param name, param info dict)
    InitialValues = t.Dict[str, t.Any]
    #   form values of one command, keyed by the python param name
    InitialsMap = t.Dict[str, InitialValues]
    #   form values of every command, keyed by the command name


class CliRunRequest:
    """
    The value the form returns when the user pressed "Run and exit".

    By then the tui has already closed, so the caller is expected to rebuild the
    command line from `command` + `tokens` and run it through the cli path. That
    way the target function's prints land on the real console, instead of being
    captured by the (now gone) log panel.
    """

    def __init__(self, command: str, tokens: t.Tuple[str, ...]) -> None:
        self.command = command
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


# The width of the name column, and the width that a small widget asks for.
# They are what the CSS below produces (a label is 18 wide, a switch takes 10,
# and a number input is 8), and they are used to pack widgets into one row.
NAME_WIDTH = 18
SWITCH_WIDTH = 10
NUMBER_WIDTH = 8

# What the form cannot hand to a row: its own horizontal padding (2 + 2) plus
# the space the params scrollbar reserves.
ROW_MARGIN = 6


def is_small(info: dict) -> bool:
    """
    Tell whether a parameter needs so little room that it can share its row
    with the parameters around it.
    """
    return info['ctype'] in (ParamType.FLAG, ParamType.NUMBER)


def widget_width(info: dict) -> int:
    """How much of a row a small parameter's widget takes."""
    if info['ctype'] is ParamType.FLAG:
        return SWITCH_WIDTH
    return NUMBER_WIDTH


def plan_layout(rows: t.Sequence[T.Row], width: int) -> t.List[t.List[T.Row]]:
    """
    Group parameters into layout rows, so that the form wastes less space.
    Each group becomes one `Horizontal`.

    A small parameter (a flag or a number) is put next to the small parameters
    that follow it, for as long as they stay neighbours and the line is not
    full. Any other parameter takes a row of its own, which also breaks the
    run - so two flags that are not neighbours never share a line.

    A group that no longer fits is closed and the next one starts on a new
    line: wrapping is done by starting a new row rather than by `flex-wrap`,
    which textual does not support.
    """
    plan: t.List[t.List[T.Row]] = []
    run: t.List[T.Row] = []
    used = 0
    for name, info in rows:
        row = (name, info)
        if not is_small(info):
            if run:
                plan.append(run)
                run, used = [], 0
            plan.append([row])
            continue
        step = NAME_WIDTH + widget_width(info)
        if run and used + step > width:
            plan.append(run)
            run, used = [], 0
        run.append(row)
        used += step
    if run:
        plan.append(run)
    return plan


def tab_id(command_name: str) -> str:
    return 'tab-{}'.format(command_name)


def pane_id(command_name: str) -> str:
    return 'pane-{}'.format(command_name)


def widget_id(command_name: str, param_name: str) -> str:
    return 'param-{}-{}'.format(command_name, param_name)


def label_id(command_name: str, param_name: str) -> str:
    return 'label-{}-{}'.format(command_name, param_name)


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
        values[name] = value if isinstance(value, bool) else _value_text(value)
    return values


def resolve_initials(
    func_infos: t.Sequence[FuncInfo], argv: t.Optional[Argv]
) -> t.Tuple[T.InitialsMap, str]:
    """
    Work out the form values of every command from a command line, and tell
    which command the command line refers to (its tab is opened first).

    Returns `(initials, active_command_name)`.
    """
    func_infos = list(func_infos)
    initials: T.InitialsMap = {fi.name: {} for fi in func_infos}
    active = func_infos[0].name
    if argv is None:
        return initials, active

    if len(func_infos) == 1:
        initials[func_infos[0].name] = collect_initial_values(
            func_infos[0], argv
        )
        return initials, active

    # multi-command: the first positional token is the command name, and the
    # tokens that follow it are that command's arguments.
    tokens = list(argv.args)
    for i, token in enumerate(tokens):
        if token.startswith(('-', '_')):
            continue
        target = next((x for x in func_infos if x.name == token), None)
        if target is not None:
            active = target.name
            sub_argv = Argv(argv.launcher, argv.target, tuple(tokens[i + 1 :]))
            initials[target.name] = collect_initial_values(target, sub_argv)
        break
    return initials, active


def _label(info: dict) -> str:
    # e.g. '--use-exist, -u' -> 'use-exist'
    return info['cname'].split(',')[0].strip().lstrip('-')


def _label_markup(info: dict) -> str:
    """
    The name column of a row. A required parameter (one without a default) is
    preceded by a red "*".
    """
    if info.get('default', ...) is ...:
        return '[red]*[/] {}'.format(_label(info))
    return _label(info)


def _value_text(value: t.Any) -> str:
    """
    The input box text that stands for a value: an empty string shows up as
    ':empty' and `None` as ':none', so that "an empty value" can be told apart
    from "nothing filled in".
    """
    if value is None:
        return ':none'
    if value == '':
        return ':empty'
    return str(value)


def _default_text(info: dict) -> str:
    value = info.get('default', ...)
    if value is ... or isinstance(value, bool):
        return ''
    return _value_text(value)


def _default_flag(info: dict) -> bool:
    return bool(info.get('default'))


def _plain(text: str) -> str:
    """
    Strip the rich markup that the cli-oriented error messages carry, so that
    they can be shown as-is in the tui.
    """
    return re.sub(r'\[/?[^\[\]]*\]', '', text)


def _default_repr(info: dict) -> t.Optional[str]:
    """
    A readable form of the default value, or `None` when the parameter has no
    default. It follows the cli help panel: `:true` / `:false` for flags,
    `""` for an empty string.
    """
    value = info.get('default', ...)
    if value is ...:
        return None
    if isinstance(value, bool):
        return ':true' if value else ':false'
    if value is None:
        return ':none'
    if value == '':
        return '""'
    return str(value)


def _tooltip(info: dict) -> Text:
    """
    The parameter's full help: its (possibly multi-line) description, plus its
    type and default value. It complements the input's placeholder, which can
    only show a single line.
    """
    text = Text()
    desc = info.get('desc') or ''
    if desc:
        text.append(desc)
        text.append('\n\n')
    text.append('type: ', style='dim')
    text.append(info['ctype'].name)
    default = _default_repr(info)
    if default is not None:
        text.append('\ndefault: ', style='dim')
        text.append(default)
    return text


class ArgsenseTuiApp(App[t.Any]):
    CSS = """
    #form {
        width: 100%;
        height: 100%;
        padding: 0 2;
    }
    #params {
        height: 1fr;
    }
    #panes {
        height: auto;
    }
    .pane {
        height: auto;
    }
    .desc {
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
    .row > .number {
        width: 8;
        /* `Input` pads by 2, which would leave only 2 visible characters in
           such a narrow box. */
        padding: 0 1;
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
        min-height: 7;
        margin-top: 1;
        border: round $primary;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ('escape', 'quit', 'Quit'),
        # pressing enter is a shortcut for the "Run" button; see
        # `action_enter_run`.
        ('enter', 'enter_run', 'Run'),
    ]

    def __init__(
        self,
        func_infos: t.Sequence[FuncInfo],
        inline: bool = False,
        initials: t.Optional[T.InitialsMap] = None,
        active: str = '',
    ) -> None:
        super().__init__()
        self.func_infos = list(func_infos)
        self.by_name = {x.name: x for x in self.func_infos}
        self.inline = inline
        self.initials = dict(initials or {})
        self.active = active or self.func_infos[0].name
        self.title = (
            self.func_infos[0].name if len(self.func_infos) == 1 else 'argsense'
        )
        self.sub_title = 'argsense'

    @property
    def active_func_info(self) -> FuncInfo:
        return self.by_name[self.active]

    def compose(self) -> ComposeResult:
        with Vertical(id='form'):
            if len(self.func_infos) > 1:
                yield Tabs(
                    *(Tab(x.name, id=tab_id(x.name)) for x in self.func_infos),
                    active=tab_id(self.active),
                    id='tabs',
                )
            with VerticalScroll(id='params'):
                with ContentSwitcher(id='panes', initial=pane_id(self.active)):
                    for func_info in self.func_infos:
                        with Vertical(
                            id=pane_id(func_info.name), classes='pane'
                        ):
                            yield from self._compose_pane(func_info)
            with Horizontal(id='actions'):
                yield Button('Run', id='run', variant='primary')
                yield Button('Run and exit', id='run-exit')
                yield Button('Exit', id='exit', variant='error')
            yield RichLog(id='log', max_lines=1000, markup=False)

    def _compose_pane(self, func_info: FuncInfo) -> ComposeResult:
        initial = self.initials.get(func_info.name, {})
        if func_info.desc:
            yield Static(func_info.desc, classes='desc')
        width = max(1, self.size.width - ROW_MARGIN)
        for group in plan_layout(collect_rows(func_info), width):
            with Horizontal(classes='row'):
                for name, info in group:
                    yield Label(
                        _label_markup(info),
                        classes='name',
                        id=label_id(func_info.name, name),
                    )
                    if info['ctype'] is ParamType.FLAG:
                        yield Switch(
                            value=bool(initial.get(name, _default_flag(info))),
                            id=widget_id(func_info.name, name),
                        )
                    else:
                        classes = (
                            'number'
                            if info['ctype'] is ParamType.NUMBER
                            else ''
                        )
                        yield Input(
                            value=str(initial.get(name, _default_text(info))),
                            placeholder=info['desc'],
                            classes=classes,
                            id=widget_id(func_info.name, name),
                        )

    def on_mount(self) -> None:
        self.query_one('#log', RichLog).border_title = 'log'
        for func_info in self.func_infos:
            for name, info in collect_rows(func_info):
                if not info.get('desc'):
                    continue
                widget = self.query_one(
                    '#{}'.format(widget_id(func_info.name, name))
                )
                widget.tooltip = _tooltip(info)
        if self.inline:
            # inline mode: the form is a fixed-height block, so nothing
            # scrolls and the log panel gets 5 lines of content (plus the two
            # border rows).
            self.query_one('#form').styles.height = 'auto'
            self.query_one('#params').styles.height = 'auto'
            self.query_one('#log', RichLog).styles.height = 7

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab is None:
            return
        self.active = (event.tab.id or '')[len('tab-') :] or self.active
        self.query_one('#panes', ContentSwitcher).current = pane_id(self.active)

    # --------------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'run':
            self.execute()
        elif event.button.id == 'run-exit':
            # hand the assembled command line back to the caller, which runs it
            # through the cli path once the tui has closed - so that the target
            # function's prints are not swallowed by the log panel.
            self.exit(CliRunRequest(self.active, tuple(self.collect_tokens())))
        elif event.button.id == 'exit':
            self.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # an input consumes the enter key itself, so the key binding above
        # never sees it - handle the message instead.
        self.action_enter_run()

    def action_enter_run(self) -> None:
        """
        Enter acts as the "Run" button, but only when the form is complete.
        Otherwise nothing happens (not even a message is logged).
        """
        if self.ready_to_run():
            self.execute()

    def ready_to_run(self) -> bool:
        """
        Tell whether every required parameter of the active command holds a
        value. Optional parameters may stay empty - their default applies.
        """
        func_info = self.active_func_info
        for name, info in collect_rows(func_info):
            if info['ctype'] is ParamType.FLAG:
                continue
            if info.get('default', ...) is not ...:
                continue
            widget = self.query_one(
                '#{}'.format(widget_id(func_info.name, name))
            )
            if isinstance(widget, Input) and not widget.value.strip():
                return False
        return True

    def collect_form_errors(self) -> t.List[str]:
        """
        Report the parameters of the active command whose input box was left
        empty. An empty box is not silently replaced by the signature default,
        so the user is told what to type instead. A required parameter (one
        without a default) is left to the parser, which reports the missing
        argument itself.
        """
        func_info = self.active_func_info
        errors: t.List[str] = []
        for name, info in collect_rows(func_info):
            if info['ctype'] is ParamType.FLAG:
                continue
            widget = self.query_one(
                '#{}'.format(widget_id(func_info.name, name))
            )
            if not isinstance(widget, Input) or widget.value.strip():
                continue
            default = info.get('default', ...)
            label = _label(info)
            if default is ...:
                continue
            elif default is None:
                errors.append(
                    "{} miss input, to pass 'empty' value, use :none".format(
                        label
                    )
                )
            elif default == '':
                errors.append(
                    "{} miss input, to pass 'empty' value, use :empty".format(
                        label
                    )
                )
            else:
                errors.append('{} is not filled'.format(label))
        return errors

    def execute(self) -> None:
        errors = self.collect_form_errors()
        if errors:
            for message in errors:
                self.write_log(Text(message, style='red'))
            return

        func_info = self.active_func_info
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
                result = func_info.target(*args, **kwargs)
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
        Assemble the command line tokens from the current form values. Only the
        active command's rows are read.
        """
        func_info = self.active_func_info
        tokens: t.List[str] = []
        for name, _info in collect_rows(func_info):
            widget = self.query_one(
                '#{}'.format(widget_id(func_info.name, name))
            )
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
        func_info = self.active_func_info
        result = parse_argv(
            Argv(('argsense',), ('tui',), tuple(self.collect_tokens())),
            mode='command',
            front_matter=front_matter(func_info),  # type: ignore
            implicit_help=False,
            raise_on_error=True,
        )
        assert result is not None
        return tuple(result['args'].values()), result['kwargs']


def run_form(
    func_infos: t.Sequence[FuncInfo],
    inline: bool = False,
    argv: t.Optional[Argv] = None,
    cli_runner: t.Optional[t.Callable[[CliRunRequest], t.Any]] = None,
) -> t.Any:
    """
    Launch the form and return the target function's return value.

    Every command in `func_infos` gets its own tab in the form.

    params:
        argv:
            an optional command line, whose values prefill the form.
        cli_runner:
            called when the user pressed "Run and exit". It should run the
            rebuilt command line through the cli path.
    """
    func_infos = list(func_infos)
    initials, active = resolve_initials(func_infos, argv)
    app = ArgsenseTuiApp(
        func_infos, inline=inline, initials=initials, active=active
    )
    result = app.run(inline=inline)
    if isinstance(result, CliRunRequest) and cli_runner is not None:
        return cli_runner(result)
    return result
