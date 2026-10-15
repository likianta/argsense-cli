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
from textual.widgets import ListItem
from textual.widgets import ListView
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
    GroupStructure = t.List[t.Tuple[str, t.List[str]]]
    #   [(group_name, [cmd_name, ...]), ...], the same shape that the cli help
    #   interface draws as a tree (see `cli.run_group`)


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


# The width of the name column of a normal row, which is also what the first
# item of a compact row takes. A name that comes after another small widget
# only takes the room its own text needs, plus `NAME_PAD` for its widget (see
# the CSS below).
NAME_WIDTH = 18
NAME_PAD = 1

# The width of the widgets that get a narrow box of their own: a switch is 10
# wide, and a number input is 12 - eight of which can be typed in (the `tall`
# border and the padding take two cells each).
SWITCH_WIDTH = 10
NUMBER_WIDTH = 12

# The fixed gap that a small widget leaves after itself in a compact row.
ITEM_GAP = 3

# What the form cannot hand to a row: its own horizontal padding (2 + 2), the
# border of the panel that wraps the form (2), plus the space the params
# scrollbar reserves.
ROW_MARGIN = 8


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


def item_width(name: str, info: dict, first: bool) -> int:
    """
    How much of a compact row one parameter takes: its name, its widget, and
    the gap that follows it.
    """
    label = NAME_WIDTH if first else len(name) + NAME_PAD
    return label + widget_width(info) + ITEM_GAP


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
        step = item_width(name, info, first=not run)
        if run and used + step > width:
            plan.append(run)
            run, used = [], 0
            # the wrapped item opens the new row, so it takes the name column.
            step = item_width(name, info, first=True)
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


def group_id(group_name: str) -> str:
    return 'group-{}'.format(group_name)


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


def _resolve_groups(
    groups: t.Optional[T.GroupStructure], func_infos: t.Sequence[FuncInfo]
) -> T.GroupStructure:
    """
    Normalise the group structure for the sidebar: drop the names that match
    no command, and collect the commands that no group mentions into a
    trailing "ungrouped" group - the same way the cli help interface does it.
    An empty result means "no sidebar".
    """
    if not groups:
        return []

    names = {x.name for x in func_infos}
    structure: T.GroupStructure = []
    used: t.Set[str] = set()
    for group_name, cmd_names in groups:
        members = [x for x in cmd_names if x in names]
        if not members:
            continue
        used.update(members)
        structure.append((group_name, members))

    leftovers = [x.name for x in func_infos if x.name not in used]
    if leftovers:
        structure.append(('ungrouped', leftovers))
    return structure


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


class GroupItem(ListItem):
    """
    One group of commands, drawn as a big button in the sidebar.

    The item is three lines tall: an outline border with the group name in the
    middle. The active group fills that border, which is what makes it look
    pressed.

    The look is styled by the app (see its CSS): it has to out-specify the
    `-highlight` rule of `ListView`, which would otherwise paint the item's
    background with the cursor color and hide the border.
    """

    def __init__(self, group_name: str) -> None:
        super().__init__(id=group_id(group_name))
        self.group_name = group_name

    def compose(self) -> ComposeResult:
        yield Label(self.group_name, classes='group-name')


class ArgsenseTuiApp(App[t.Any]):
    CSS = """
    #form {
        width: 100%;
        height: 100%;
        padding: 0 2;
    }
    #panel {
        /* everything above the run buttons lives in a bordered panel. */
        height: 1fr;
        border: round $primary;
    }
    #body {
        layout: horizontal;
        height: 100%;
    }
    #sidebar {
        width: 22;
        height: 100%;
        margin-right: 1;
        border-right: solid $surface-lighten-2;
        background: transparent;
    }
    #main {
        width: 1fr;
        height: 100%;
    }
    /* the sidebar is the only place where group items are used, and the
       `#sidebar` prefix is what out-specifies the `-highlight` rule that
       `ListView` brings (which would otherwise tint the item with the cursor
       color and wash its border out). */
    #sidebar > GroupItem {
        height: 3;
        border: round $surface-lighten-2;
        background: transparent;
        color: $text-muted;
        content-align: center middle;
    }
    #sidebar > GroupItem.-highlight {
        /* the list view cursor: a faint tint, so that it does not read as
           "this is the active group". */
        background: $surface;
        color: $text;
    }
    #sidebar > GroupItem.-active {
        /* a pressed button: the border stays the bright accent, and the fill
           is a darker shade of it - using the accent for both would make the
           border invisible. */
        border: round $primary;
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
    }
    #sidebar > GroupItem > .group-name {
        width: 100%;
        text-align: center;
    }
    #params {
        width: 100%;
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
    .row > .name-inline {
        /* a name that comes after a small widget: it only takes the room its
           own text needs, so that the widgets around it keep an even gap. */
        width: auto;
        padding: 1 1 0 0;
        color: $text-muted;
    }
    .row > Input {
        width: 1fr;
    }
    .row > .number {
        /* eight cells to type in. the `tall` border and the padding take two
           cells each, so the box itself is twelve wide. */
        width: 12;
        padding: 0 1;
    }
    .row > Switch {
        width: auto;
    }
    .row > .small {
        /* the gap between two small widgets of the same row. */
        margin-right: 3;
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
        /* two fifths of the window (the margin above it is part of it). the log
           used to share the space with the form evenly, which made it two rows
           taller than the parameter area (the tab bar takes those two rows from
           the form). the form, as `1fr`, takes whatever is left. */
        height: 40%;
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
        groups: t.Optional[T.GroupStructure] = None,
    ) -> None:
        super().__init__()
        self.func_infos = list(func_infos)
        self.by_name = {x.name: x for x in self.func_infos}
        self.inline = inline
        self.initials = dict(initials or {})
        self.groups = _resolve_groups(groups, self.func_infos)
        self.group_of = {
            name: group_name
            for group_name, names in self.groups
            for name in names
        }
        self.members_of = dict(self.groups)
        self.has_tabs = len(self.func_infos) > 1
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
            with Vertical(id='panel'):
                with Horizontal(id='body'):
                    if self.groups:
                        # the sidebar picks the group; the tab bar next to it
                        # shows the commands of that group (see `activate`).
                        yield ListView(
                            *(GroupItem(x) for x, _ in self.groups),
                            id='sidebar',
                        )
                    with Vertical(id='main'):
                        if self.has_tabs:
                            # `active` is not passed here: `on_mount` takes
                            # care of it, once the layout is known (`Tabs` can
                            # only scroll the active tab into view when the
                            # tabs have a region).
                            yield Tabs(
                                *(
                                    Tab(x.name, id=tab_id(x.name))
                                    for x in self.func_infos
                                ),
                                id='tabs',
                            )
                        with VerticalScroll(id='params'):
                            with ContentSwitcher(
                                id='panes', initial=pane_id(self.active)
                            ):
                                for func_info in self.func_infos:
                                    with Vertical(
                                        id=pane_id(func_info.name),
                                        classes='pane',
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
            # a row that several small widgets share. The first one keeps the
            # name column (so that it lines up with the rows around it), the
            # others only take what their own name needs, and every widget
            # leaves the same gap after itself (see the CSS).
            compact = len(group) > 1
            with Horizontal(classes='row'):
                for index, (name, info) in enumerate(group):
                    yield Label(
                        _label_markup(info),
                        classes='name' if index == 0 else 'name-inline',
                        id=label_id(func_info.name, name),
                    )
                    extra = ' small' if compact else ''
                    if info['ctype'] is ParamType.FLAG:
                        yield Switch(
                            value=bool(initial.get(name, _default_flag(info))),
                            classes=extra.strip(),
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
                            classes=(classes + extra).strip(),
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
            self.query_one('#panel').styles.height = 'auto'
            self.query_one('#body').styles.height = 'auto'
            self.query_one('#main').styles.height = 'auto'
            self.query_one('#params').styles.height = 'auto'
            self.query_one('#log', RichLog).styles.height = 7
        # the command line may have picked a command of a group that is not the
        # first one, so the sidebar and the tab bar have to catch up. it is
        # deferred by one refresh, because scrolling to a tab or to a group
        # item needs their regions, and those are only known after the first
        # layout pass.
        self.call_after_refresh(self.activate, self.active)

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab is None:
            return
        name = (event.tab.id or '')[len('tab-') :]
        if name:
            self.activate(name)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        A sidebar item was clicked (or confirmed with enter): open that group.
        Its first command is opened, unless the active one is already a member
        of it.
        """
        item = event.item
        if not isinstance(item, GroupItem):
            return
        members = self.members_of[item.group_name]
        if self.active not in members:
            self.activate(members[0])

    def activate(self, command_name: str) -> None:
        """
        Show the pane of `command_name`, bring its group to the front, and
        scroll the command's tab and its group's sidebar item into view.
        """
        if command_name not in self.by_name:
            return
        self.active = command_name
        self.query_one('#panes', ContentSwitcher).current = pane_id(
            command_name
        )
        if self.groups:
            self.activate_group(self.group_of[command_name])
        elif self.has_tabs:
            self.query_one('#tabs', Tabs).active = tab_id(command_name)

    def activate_group(self, group_name: str) -> None:
        """
        Make `group_name` the group on show: its item is the active one in the
        sidebar, and the tab bar only shows its commands.
        """
        index = [x for x, _ in self.groups].index(group_name)
        for item in self.query(GroupItem):
            item.set_class(item.group_name == group_name, '-active')
        # assigning `index` also scrolls the item into view.
        self.query_one(ListView).index = index

        if not self.has_tabs:
            return
        tabs = self.query_one('#tabs', Tabs)
        # order matters: the new active tab must be visible before it becomes
        # the active one, otherwise `Tabs` can not scroll it into view. and
        # the tabs that are hidden afterwards must not be the active one -
        # `Tabs.hide` would activate a neighbour instead.
        for name in self.members_of[group_name]:
            tabs.show(tab_id(name))
        tabs.active = tab_id(self.active)
        for name in self.by_name:
            if name not in self.members_of[group_name]:
                tabs.hide(tab_id(name))

    # --------------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ''
        if button_id == 'run':
            self.execute()
        elif button_id == 'run-exit':
            # hand the assembled command line back to the caller, which runs it
            # through the cli path once the tui has closed - so that the target
            # function's prints are not swallowed by the log panel.
            self.exit(CliRunRequest(self.active, tuple(self.collect_tokens())))
        elif button_id == 'exit':
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
    groups: t.Optional[T.GroupStructure] = None,
) -> t.Any:
    """
    Launch the form and return the target function's return value.

    Every command in `func_infos` gets its own tab in the form - unless
    `groups` is given, in which case the tab bar is replaced by the sidebar.

    params:
        argv:
            an optional command line, whose values prefill the form.
        cli_runner:
            called when the user pressed "Run and exit". It should run the
            rebuilt command line through the cli path.
        groups:
            when given, the commands are listed in a sidebar instead of the
            tab bar, and each group starts expanded.
    """
    func_infos = list(func_infos)
    initials, active = resolve_initials(func_infos, argv)
    app = ArgsenseTuiApp(
        func_infos,
        inline=inline,
        initials=initials,
        active=active,
        groups=groups,
    )
    result = app.run(inline=inline)
    if isinstance(result, CliRunRequest) and cli_runner is not None:
        return cli_runner(result)
    return result
