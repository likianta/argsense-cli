"""
The sizes a gui form asks for.

Everything here is in css px -- the unit the page lays out in, and the unit
`streamlit_canary.run(window_size=...)` takes.

The numbers come from measuring the form: a parameter row is its label line
over its control (28 + 32, the latter being the control height), and rows sit
one `--st-vgap` apart, so every row comes to 60 no matter what it holds. The
window is then that many rows plus everything stacked around them.

Note:
    `plan_rows` (in `fields.py`) packs the form with `window_row_capacity`,
    and `estimate_window_size` counts the rows with it as well, so the form
    and the window agree on the shape. Change one, look at the other.
"""

import typing as tp

NARROW_WINDOW_WIDTH = 700
WIDE_WINDOW_WIDTH = 980
#   A form that is all there is to show (no command-group sidebar) gets the
#   narrow window; one with the sidebar gets the wide one -- and the width
#   also decides how many small widgets share a row (see
#   `window_row_capacity`).

MIN_WINDOW_HEIGHT = 600
MAX_WINDOW_HEIGHT_RATIO = 0.9
#   Never shorter than the first, never taller than that much of the screen:
#   a two-row form still gets a usable window, a long one still fits.

PARAM_ROW_HEIGHT = 60
PARAM_ROW_GAP = 16
#   One parameter row is its label line over its control -- 28 + 32, the
#   latter being `--st-control-height` in canary -- and rows sit one
#   `--st-vgap` apart.

LOG_PANEL_HEIGHT_TALL = 300
LOG_PANEL_HEIGHT_SHORT = 200
LOG_PANEL_TALL_THRESHOLD = 250
#   The log panel follows the form: a tall one (250px of parameter rows or
#   more) gets the tall panel, a short one the short panel.

DOCK_EXTRA_HEIGHT = 85
#   What the bottom dock adds around the log panel: 13px padding, the Run row
#   (32px), a gap, the panel, 24px padding.

CHROME_TOP_HEIGHT = 200
CARD_BOTTOM_HEIGHT = 17
DOCK_BOTTOM_HEIGHT = 16
#   Everything the window stacks around the parameter rows: 200px above the
#   first row (the page's 32px top padding, the title band, the group row,
#   the command's caption, the card's own padding), 17px of card padding
#   below the last one, then the dock and the 16px it keeps below itself.


def window_row_capacity(wide: bool) -> int:
    """How many small widgets share a row: 2 when narrow, 4 when wide."""
    return 4 if wide else 2


def param_rows_height(rows: int) -> int:
    """How tall `rows` parameter rows come out, gaps included, in css px."""
    return rows * PARAM_ROW_HEIGHT + max(rows - 1, 0) * PARAM_ROW_GAP


def log_panel_height(rows: int) -> int:
    """The log panel height a form of `rows` parameter rows deserves."""
    if param_rows_height(rows) >= LOG_PANEL_TALL_THRESHOLD:
        return LOG_PANEL_HEIGHT_TALL
    return LOG_PANEL_HEIGHT_SHORT


def chrome_height(log_height: int) -> int:
    """Everything the window stacks around the parameter rows, in css px.

    It is what the app measures and reports to the estimator, since the
    estimator cannot see the component tree.
    """
    return (
        CHROME_TOP_HEIGHT
        + CARD_BOTTOM_HEIGHT
        + log_height
        + DOCK_EXTRA_HEIGHT
        + DOCK_BOTTOM_HEIGHT
    )


def estimate_window_size(
    rows: int, *, wide: bool = False, extra_height: int = 0
) -> tp.Tuple[int, int]:
    """
    The window size a form of `rows` parameter rows wants, in css px.

    Args:
        rows:
            the most rows any one command needs -- that one decides, since
            the app shows one at a time. Count them with
            `window_row_capacity(wide)`, so the form and the window agree on
            the shape.
        wide:
            whether the app has a command-group sidebar.
        extra_height:
            everything stacked around those rows -- what sits above them, the
            Run row, the log panel (see `chrome_height`).

    Returns:
        `(width, height)`: `NARROW_WINDOW_WIDTH` or `WIDE_WINDOW_WIDTH`, and
        the estimated height kept within `MIN_WINDOW_HEIGHT` and
        `MAX_WINDOW_HEIGHT_RATIO` of the screen.
    """
    height = param_rows_height(rows) + extra_height
    _, screen_height = screen_size_in_css_px()
    max_height = round(screen_height * MAX_WINDOW_HEIGHT_RATIO)
    height = round(max(MIN_WINDOW_HEIGHT, min(height, max_height)))
    return (WIDE_WINDOW_WIDTH if wide else NARROW_WINDOW_WIDTH), height


def screen_size_in_css_px() -> tp.Tuple[int, int]:
    """
    The usable screen in css px (pyapp-window leaves the taskbar out).

    `get_screen_size` reads the primary display in logical (css) px --
    deliberately, so that the answer does not depend on whether the calling
    process told Windows it is DPI aware -- which is the unit everything here
    is in.
    """
    from pyapp_window.util import get_screen_size

    return get_screen_size()
