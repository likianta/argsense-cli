"""
The page: how a command table becomes a form, and how Run calls a command.

A canary v3 app function runs *once*: it builds the whole component tree, and
everything after that is events and property patches. So the form is built up
front here -- every command's pane, all but the picked one hidden -- and the
scene is the registry that build fills in and Run reads back.
"""

import typing as tp
from datetime import datetime
from functools import partial

import streamlit_canary as sc
from streamlit_canary import components_v3 as v3

from .fields import SKIP
from .fields import param_field
from .fields import plan_rows
from .fields import read_param
from .layout import chrome_height
from .layout import estimate_window_size
from .layout import log_panel_height
from .layout import window_row_capacity
from .spec import Command
from .spec import Param
from .spec import resolve_groups
from .spec import spec_of
from ...cli import DEFAULT_GUI_PORT
from ...parser import FuncInfo

GroupStructure = tp.List[tp.Tuple[str, tp.List[str]]]
SceneGroups = tp.List[tp.Tuple[str, tp.Tuple[Command, ...]]]
# the two layouts canary's `PageTitle` takes: `wide` lets the page use the
# whole window, which is what a form with a sidebar wants.
Layout = tp.Literal['centered', 'wide']


class _State(sc.StateV2):
    """What the gui itself remembers: which command group is on show."""

    group: sc.Property[str]


class GuiScene:
    """
    A command table laid out for the gui: the specs, the sizes they ask for,
    and the widgets the form builds from them.

    A scene is built *before* the page runs, because the window is sized to
    the form (see `layout`) and because a canary component cannot be created
    once the runtime has built the tree.
    """

    def __init__(self, groups: SceneGroups) -> None:
        if not groups:
            raise RuntimeError('the gui needs at least one command.')

        self.groups = groups
        self.commands = tuple(
            command for _, commands in groups for command in commands
        )
        self.members: tp.Dict[str, tp.Tuple[Command, ...]] = dict(groups)
        self.group_of = {
            command.name: name
            for name, commands in groups
            for command in commands
        }

        # The sidebar is what makes the window wide: with a single group there
        # is nothing to pick, so the form drops it and the window turns
        # narrow -- which also means fewer widgets to a row, and so more rows.
        self.wide = len(groups) > 1
        self.max_per_row = window_row_capacity(self.wide)
        # the command that needs the most rows is the one that decides, since
        # the app shows one at a time.
        self.max_param_rows = max(
            len(plan_rows(command.params, self.max_per_row))
            for command in self.commands
        )
        self.log_height = log_panel_height(self.max_param_rows)
        self.window_size = estimate_window_size(
            self.max_param_rows,
            wide=self.wide,
            extra_height=chrome_height(self.log_height),
        )

        # what the form registers while it is being built, and what Run reads
        # back. nothing is looked up by name at run time: a canary component
        # cannot be created after the build.
        self.fields: tp.Dict[str, tp.Dict[str, tp.Any]] = {}
        self.tabs: tp.Dict[str, tp.Any] = {}
        self.touched: tp.Set[str] = set()
        self.logger: tp.Optional[v3.LogPanel] = None

        self.state = _State()
        self.state.group.set(groups[0][0])

    # --------------------------------------------------------------------------
    # the page

    def setup_ui(self, title: str = '', layout: Layout = 'centered') -> None:
        """
        Build the whole form. The runtime calls this once, and only once.
        """
        if title:
            v3.PageTitle(title, layout=layout)

        if self.wide:
            self._setup_sidebar()
        else:
            # one group: its pane is the whole form
            with v3.Container(border=True):
                self._group_pane(self.groups[0][0])

        with v3.BottomContainer():
            with v3.Row('center'):
                run = v3.Button('Run', type='primary', width='stretch')
            # the panel captures what the app prints, and carries its own
            # "clear" button, so it only holds this hint until then
            self.logger = v3.LogPanel(
                height=self.log_height, placeholder='No output yet.'
            )
        run.on_click.connect(self.run_command)

    def _setup_sidebar(self) -> None:
        """
        The card: the group sidebar next to the picked group's pane.

        Every group's pane is built up front and all but the picked one are
        hidden -- a canary component cannot be created after the runtime has
        built the tree, so nothing here is built on demand.
        """
        with v3.Container(border=True):
            with v3.Row('top'):
                with v3.Column(
                    border=True,
                    # hug the radio group's own width, kept inside 150..250
                    width='content',
                    min_width=150,
                    max_width=250,
                    height='stretch',
                ):
                    v3.RadioGroup(
                        'Select group',
                        tuple(name for name, _ in self.groups),
                        value=sc.bbind(self.state.group),
                        width='stretch',
                    )
                with v3.Column(weight=1):
                    for name, _ in self.groups:
                        with v3.Column(
                            visible=sc.bind(self.state.group, _equals(name))
                        ):
                            self._group_pane(name)

    def _group_pane(self, group_name: str) -> None:
        """The picked group's pane: its commands as tabs, or as the only one."""
        commands = self.members[group_name]
        if len(commands) == 1:
            # a bar with a single tab says nothing the pane does not; the tui
            # leaves it out too.
            self._command_pane(commands[0])
            return
        with v3.Tabs(tuple(command.name for command in commands)) as tabs:
            self.tabs[group_name] = tabs
            for command in commands:
                with next(tabs):
                    self._command_pane(command)

    def _command_pane(self, command: Command) -> None:
        """One command's pane: its description over its parameters."""
        v3.Caption(command.desc)
        fields = self.fields.setdefault(command.name, {})
        for row in plan_rows(command.params, self.max_per_row):
            if len(row) == 1:
                param = row[0]
                fields[param.name] = param_field(
                    param, self._change_handler(command, param)
                )
                continue
            # `bottom` alignment puts the boxes of a shared row on one line
            # even though the labels above them differ in height. Every field
            # also gets a `weight=1` column of its own, because a
            # `width='stretch'` widget inside a row still grows from its
            # type's basis (`8rem` for the input-like ones) -- four number
            # boxes would not fit one line at that basis and the fourth would
            # wrap onto a line of its own, stretching across it. The columns
            # divide the line up front instead (basis 0), which is the even
            # split the row is after.
            with v3.Row('bottom'):
                for param in row:
                    with v3.Column(weight=1):
                        fields[param.name] = param_field(
                            param, self._change_handler(command, param)
                        )

    def _change_handler(
        self, command: Command, param: Param
    ) -> tp.Callable[[], None]:
        """
        The handler a number box reports a real edit with (see `param_field`).

        It records the `command.param` key in `touched`, which is how
        `read_param` tells "still at the seed" from "set to the seed on
        purpose".
        """
        key = self.key_of(command, param)
        return lambda: self.touched.add(key)

    # --------------------------------------------------------------------------
    # running a command

    def command_at(self, group_name: str) -> tp.Optional[Command]:
        """The command whose tab is open in `group_name`."""
        if group_name not in self.members:
            return None
        commands = self.members[group_name]
        if len(commands) == 1:
            return commands[0]
        active = str(self.tabs[group_name].active.get())
        return next((x for x in commands if x.name == active), commands[0])

    def collect(
        self, command: Command
    ) -> tp.Tuple[tp.Dict[str, tp.Any], tp.List[str]]:
        """The form as a kwargs dict, plus the errors that block the run."""
        kwargs: tp.Dict[str, tp.Any] = {}
        errors: tp.List[str] = []
        fields = self.fields[command.name]
        for param in command.params:
            value = read_param(
                param,
                fields[param.name],
                touched=self.touched,
                key=self.key_of(command, param),
            )
            if value is SKIP:
                if param.required:
                    errors.append('{} is required'.format(param.name))
                continue
            kwargs[param.name] = value
        return kwargs, errors

    def run_command(self) -> None:
        """
        Call the open command with what the form holds (the Run button).

        Whatever the command prints lands in the log panel: the runtime tees
        the app's `stdout` into every `LogPanel` following it, so a command's
        own `print` shows up below without this method doing anything about
        it.
        """
        command = self.command_at(str(self.state.group.get()))
        if command is None:
            return
        if self.logger is not None:
            # a rule with the time on it, so a run's output is told apart
            # from the one before it
            self.logger.push_divider(datetime.now().strftime('%H:%M:%S'))

        kwargs, errors = self.collect(command)
        print('$ {} {}'.format(command.name, _format_kwargs(kwargs)))
        if errors:
            for error in errors:
                print(': {}'.format(error))
            return
        try:
            result = command.func(**kwargs)
        except Exception as exc:  # noqa: BLE001
            print(': {}: {}'.format(type(exc).__name__, exc))
            return
        print(': done' if result is None else ': done -> {!r}'.format(result))

    @staticmethod
    def key_of(command: Command, param: tp.Any) -> str:
        """The `command.param` key that stands for one widget."""
        return '{}.{}'.format(command.name, param.name)


def _equals(group_name: str) -> tp.Callable[[tp.Any], bool]:
    return lambda value: value == group_name


def _format_kwargs(kwargs: tp.Dict[str, tp.Any]) -> str:
    return ' '.join('{}={!r}'.format(k, v) for k, v in kwargs.items())


def run_form(
    func_infos: tp.Sequence[FuncInfo],
    *,
    groups: tp.Optional[GroupStructure] = None,
    title: str = 'argsense',
    port: int = DEFAULT_GUI_PORT,
    window: bool = False,
) -> None:
    """
    Open the form on `func_infos` and serve it.

    params:
        groups:
            the cli's group structure (see `cli.run_group`). Given, the groups
            are listed in a sidebar; left out, the commands make up one flat
            group and there is no sidebar.
        title:
            the page's title, and the native window's title bar.
        port:
            the port the app is served on.
        window:
            whether to open the form in a native window, sized to the form
            itself, instead of serving it for a browser tab.
    """
    commands = [spec_of(func_info) for func_info in func_infos]
    scene = GuiScene(resolve_groups(groups, commands))
    layout: Layout = 'wide' if window else 'centered'
    sc.run(
        partial(scene.setup_ui, title, layout),
        port=port,
        show_window=window,
        window_size=scene.window_size,
        window_title=title or None,
    )
