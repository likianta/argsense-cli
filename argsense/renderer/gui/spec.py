"""
The form's specification: one `Param` per parameter of a command, read off
the command's `FuncInfo`.

The reading is the one the tui does (see `renderer/tui/app.py`): `args0`
(required positional) -> `args1` (positional with a default) -> `args3`
(keyword-only), with the variadic ones (`args2` / `args4`) left out, because a
form cannot draw an unbounded list.
"""

import typing as tp

from ...parser import FuncInfo

# the widgets a parameter can ask for.
TEXT = 'text'
NUMBER = 'number'
MAYBE_NUMBER = 'maybe-number'
FLAG = 'flag'
TRIPLE = 'triple'

# argsense's own classification (`plain_type`) -> our kind. `optional-flag` is
# its name for a `bool | None`: the one type the command line cannot spell (a
# flag has only two states), which is why it gets a widget of its own.
KIND_OF_PLAIN_TYPE: tp.Dict[str, str] = {
    'str': TEXT,
    'int': NUMBER,
    'float': NUMBER,
    'flag': FLAG,
    'optional-flag': TRIPLE,
}

# A switch has no room for words, so each state wears a coloured material
# icon instead: a red cross for False, an orange "blocked" for None, a green
# tick for True. A `bool` switch shows the first and the last; a
# `bool | None` one shows all three (the command line cannot spell that
# middle state, which is the whole reason it gets a widget).
MARK_FALSE = ':red[:material/cancel:]'
MARK_NONE = ':orange[:material/block:]'
MARK_TRUE = ':green[:material/check_circle:]'

# the group a command is collected into when no group mentions it (see
# `resolve_groups`), and the name of the single group a scene without groups
# is given -- a name that is never shown, since a lone group draws no
# sidebar.
UNGROUPED = 'ungrouped'
FLAT_GROUP = 'commands'


class Param:
    """One parameter of a command: what to draw, and how to read it back."""

    def __init__(
        self,
        name: str,
        kind: str,
        plain_type: str,
        default: tp.Any,
        desc: str,
        required: bool,
        short: str,
    ) -> None:
        self.name = name
        self.kind = kind
        self.plain_type = plain_type
        self.default = default
        self.desc = desc
        self.required = required
        self.short = short

    @property
    def label(self) -> str:
        """The widget label: the name, its short flag, and a required mark."""
        out = self.name
        if self.short:
            out += ' :gray[({})]'.format(self.short)
        if self.required:
            out += ' :red[*]'
        return out

    @property
    def seed(self) -> tp.Any:
        """The number a `NumberInput` starts at (see `read_param`).

        A parameter with a default starts there. One without -- a required
        `port` -- starts at a zero of its own type, which is a placeholder on
        screen and nothing more: `read_param` drops it again while the user
        has not touched the box. (A number that may be absent never gets a
        `NumberInput` at all -- see `MAYBE_NUMBER`.)
        """
        if self.default is not None:
            return self.default
        return 0.0 if self.plain_type == 'float' else 0


class Command:
    """One command: its name, one-line description, function and parameters."""

    def __init__(
        self,
        name: str,
        desc: str,
        func: tp.Callable[..., tp.Any],
        params: tp.List[Param],
    ) -> None:
        self.name = name
        self.desc = desc
        self.func = func
        self.params = params


def spec_of(func_info: FuncInfo) -> Command:
    """Read one command off its `FuncInfo` -- the same read the tui does."""
    params: tp.List[Param] = []
    for name, raw in _collect_raw(func_info):
        plain_type = raw.get('plain_type', '')
        default = raw.get('default', ...)
        # a parameter without a default is a required one. `fill_docs_info`
        # gives the parameters it recovers from a `**kwargs` description the
        # `...` sentinel, which reads the same way.
        required = default is ...
        if required:
            default = None
        params.append(
            Param(
                name=name,
                kind=kind_of(plain_type, required=required, default=default),
                plain_type=plain_type,
                default=default,
                # the human description comes from the docstring's `params:`
                # block, which `fill_docs_info` has already merged in.
                desc=raw.get('desc', ''),
                required=required,
                short=short_flag_of(raw.get('cname', '')),
            )
        )
    return Command(func_info.name, func_info.desc, func_info.target, params)


def _collect_raw(func_info: FuncInfo) -> tp.List[tp.Tuple[str, dict]]:
    return [
        *func_info.args0.items(),
        *func_info.args1.items(),
        *func_info.args3.items(),
    ]


def kind_of(plain_type: str, *, required: bool, default: tp.Any) -> str:
    """The widget kind a `plain_type` asks for."""
    kind = KIND_OF_PLAIN_TYPE.get(plain_type, TEXT)
    if kind == NUMBER and not required and default is None:
        # a number that may be absent. argsense reports `int | None` as a
        # plain `int` whose default is None, and a number box cannot be
        # emptied -- so this one is drawn as a text box, whose emptiness
        # means what the tui's unfilled field means (see `read_param`).
        return MAYBE_NUMBER
    return kind


def short_flag_of(cname: str) -> str:
    """`'--verbose, -v'` -> `'-v'`, and `''` when there is no short flag."""
    for part in cname.split(','):
        part = part.strip()
        if len(part) == 2 and part.startswith('-'):
            return part
    return ''


def resolve_groups(
    groups: tp.Optional[tp.List[tp.Tuple[str, tp.List[str]]]],
    commands: tp.Sequence[Command],
) -> tp.List[tp.Tuple[str, tp.Tuple[Command, ...]]]:
    """
    Turn the cli's group structure into `[(group_name, (Command, ...)), ...]`.

    A structure that mentions no command is dropped, and the commands that no
    group mentions are collected into a trailing "ungrouped" group -- the same
    way the tui sidebar and the cli help interface do it. No structure at all
    (a plain `cli.run`) means one flat group, which draws no sidebar.
    """
    if not groups:
        return [(FLAT_GROUP, tuple(commands))]

    by_name = {command.name: command for command in commands}
    structure: tp.List[tp.Tuple[str, tp.Tuple[Command, ...]]] = []
    used: tp.Set[str] = set()
    for group_name, cmd_names in groups:
        members = tuple(by_name[x] for x in cmd_names if x in by_name)
        if not members:
            continue
        used.update(command.name for command in members)
        structure.append((group_name, members))

    leftovers = tuple(x for x in commands if x.name not in used)
    if leftovers:
        structure.append((UNGROUPED, leftovers))
    return structure
