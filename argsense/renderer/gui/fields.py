"""
Drawing one parameter, and reading it back.

`param_field` turns a `Param` into the canary widget that suits its kind,
`plan_rows` and `row_slots` decide how those widgets share the form's lines,
and `read_param` turns a widget back into the value the command is called
with, at the moment Run is pressed (see `app.GuiScene.run_command`).
"""

import typing as tp

from streamlit_canary import components_v3 as v3

from .layout import QUARTERS_PER_ROW
from .spec import FLAG
from .spec import MAYBE_NUMBER
from .spec import MARK_FALSE
from .spec import MARK_NONE
from .spec import MARK_TRUE
from .spec import NUMBER
from .spec import TEXT
from .spec import TRIPLE
from .spec import Param

# ---------------------------------------------------------------------------
# How much of a row a widget asks for
# ---------------------------------------------------------------------------
# A row is `QUARTERS_PER_ROW` quarter-width slots wide, and a widget's kind
# says how it takes them -- which is what the shared rows are built from (see
# `plan_rows` and `row_slots`).

LONG = 'long'
#   The row to itself: a text box is wide enough that sharing a line would
#   leave every box on it too narrow to read.
VARIABLE = 'variable'
#   An equal share of the line, whatever its neighbours leave it -- a number
#   box reads fine at any width.
SHORT = 'short'
#   One quarter, always: a switch is a fixed rail of two or three marks, so it
#   is the same width wherever it sits.

WIDTH_CLASS_OF_KIND: tp.Dict[str, str] = {
    TEXT: LONG,
    NUMBER: VARIABLE,
    MAYBE_NUMBER: VARIABLE,
    FLAG: SHORT,
    TRIPLE: SHORT,
}


class _Skip:
    """
    "The form does not spell this parameter."

    It is left out of the call, so the command's own default applies (and a
    required one is an error).
    """

    def __repr__(self) -> str:
        return 'SKIP'


SKIP = _Skip()


def plan_rows(params: tp.Sequence[Param]) -> tp.List[tp.List[Param]]:
    """
    Split the parameters into rows, `QUARTERS_PER_ROW` widgets to a row.

    A run of consecutive sharing widgets (numbers and switches) fills one row
    after another; a long widget (a text input) takes a row of its own, which
    also ends the run before it -- so two widgets that are not neighbours
    never end up together.
    """
    rows: tp.List[tp.List[Param]] = []
    run: tp.List[Param] = []
    for param in params:
        if WIDTH_CLASS_OF_KIND[param.kind] == LONG:
            if run:
                rows.append(run)
                run = []
            rows.append([param])
            continue
        run.append(param)
        if len(run) == QUARTERS_PER_ROW:
            rows.append(run)
            run = []
    if run:
        rows.append(run)
    return rows


def row_slots(row: tp.Sequence[Param]) -> tp.Tuple[tp.List[int], int]:
    """
    The quarter-width slots each widget of a row takes, and the ones left
    over.

    A switch always takes one. The number boxes share what the switches leave
    of the four between them, equally and rounded down -- the odd slot of an
    uneven share stays empty rather than stretching them, so one box beside
    two switches comes out 2:1:1, and two boxes beside one switch comes out
    1:1:1 with a quarter to spare.

    The leftover is handed back rather than spent: a row that does not fill
    its four slots has to say so, or the flex layout would widen the widgets
    that are in it until it did.
    """
    classes = [WIDTH_CLASS_OF_KIND[param.kind] for param in row]
    if len(row) == 1 and classes[0] == LONG:
        # a long widget is alone in its row, and the whole line is its
        return [QUARTERS_PER_ROW], 0
    shorts = classes.count(SHORT)
    variables = len(row) - shorts
    if variables == 0:
        slots = [1] * len(row)
    else:
        share = (QUARTERS_PER_ROW - shorts) // variables
        slots = [1 if x == SHORT else share for x in classes]
    return slots, QUARTERS_PER_ROW - sum(slots)


def param_field(
    param: Param, on_change: tp.Optional[tp.Callable[[], None]] = None
) -> tp.Any:
    """
    Draw one parameter's widget and return it (its value's holder).

    `on_change` is connected to a `NumberInput`'s own change event, and only
    there: a number box cannot be emptied, so that event is the only way to
    tell "left at the seed" from "set to that value on purpose" (see
    `read_param`).
    """
    if param.kind in (TEXT, MAYBE_NUMBER):
        # both are text boxes. The absent-able number reads an empty box as
        # "leave this parameter out" (see `read_param`), which is why it is
        # not a number box: that one cannot be emptied.
        value = '' if param.default is None else str(param.default)
        return v3.TextInput(param.label, value, help=param.desc)

    if param.kind == NUMBER:
        field = v3.NumberInput(
            param.label, param.seed, width='stretch', help=param.desc
        )
        if on_change is not None:
            field.value.on_change.connect(on_change)
        return field

    if param.kind == FLAG:
        return v3.SegmentedControl(
            param.label,
            (MARK_FALSE, MARK_TRUE),
            index=double_index_of(param.default),
            width='content',
            help=param.desc,
        )

    return v3.SegmentedControl(
        param.label,
        (MARK_FALSE, MARK_NONE, MARK_TRUE),
        index=triple_index_of(param.default),
        width='content',
        help=param.desc,
    )


def double_index_of(default: tp.Any) -> int:
    """`SegmentedControl` from a value to an index: False/True -> 0/1."""
    return 1 if default is True else 0


def triple_index_of(default: tp.Any) -> int:
    """`SegmentedControl` from a value to an index: False/None/True -> 0/1/2."""
    if default is None:
        return 1
    return 2 if default else 0


def read_param(
    param: Param, field: tp.Any, *, touched: tp.Set[str], key: str
) -> tp.Any:
    """One parameter's value, or `SKIP` when the form does not spell it."""
    if param.kind == TEXT:
        # a text box with nothing in it is exactly the "not filled in" state
        # the tui's form refuses to run with (when the parameter is required)
        return str(field.value.get() or '') or SKIP
    elif param.kind == MAYBE_NUMBER:
        # the same emptiness, read as "leave the parameter out": the call then
        # leaves it to the command's own `None`
        text = str(field.value.get() or '')
        return SKIP if not text.strip() else value_of(text)
    elif param.kind == NUMBER:
        if key in touched:
            return field.value.get()
        # untouched: the box still shows the seed. That is a real default for
        # most parameters, but a mere placeholder for one that has none --
        # and for a required `port` it is `SKIP`, so Run refuses rather than
        # opening a server on port 0.
        return SKIP if param.default is None else param.default
    elif param.kind == FLAG:  # SegmentedControl[False, True]
        return field.index.get() == 1
    else:  # SegmentedControl[False, None, True]
        return (False, None, True)[field.index.get()]


def value_of(text: str) -> tp.Any:
    """
    Read a text box's content as a value, leniently.

    A leading `:` asks for a value rather than text -- `:true` is the
    boolean, `:none` / `:null` is `None`, the words json spells them with.
    Otherwise the text is tried as a number in any of python's own notations
    (`0xABCD`, `0b1101`, `0o755`, `1_000`, `1e3`); failing that it is handed
    over as written. The command knows what it asked for, and its own error
    says so far more clearly than a "not a number" refusal here would.
    """
    text = text.strip()
    if text.startswith(':'):
        word = text[1:].strip()
        if word.lower() in ('true', 'false'):
            return word.lower() == 'true'
        elif word.lower() in ('none', 'null'):
            return None
        else:
            return text
    # base 0 is what spells 0x / 0b / 0o and the digit grouping python allows
    # (`1_000`); base 10 catches what it refuses to read that way (`08`)
    for base in (0, 10):
        try:
            return int(text, base)
        except ValueError:
            pass
    try:
        return float(text)
    except ValueError:
        return text
