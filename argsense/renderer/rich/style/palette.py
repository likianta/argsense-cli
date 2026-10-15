"""
The color tables used by the rich renderer.

Two palettes are maintained, and `get_palette()` picks one for the console in
use:

    ModernPalette
        For the terminals that can show truecolor. The colors are the 'mocha'
        flavour of the catppuccin palette (https://catppuccin.com/palette),
        and the titles are drawn as a gradient.

    LegacyPalette
        For every other terminal - the 256-color ones, the plain 16-color
        ones, and the legacy windows console. It only uses color names that
        all of them understand, and it draws the titles in a single color:
        a gradient would come out as noise there.

The detection is delegated to rich, which already knows whether the console
is the legacy windows one (see `rich.console.detect_legacy_windows`) and
which color system it supports (see `rich.console.Console.color_system`). A
legacy windows console is reported as `ColorSystem.WINDOWS`, so it never
looks like a truecolor one.
"""

import typing as tp

from rich import get_console
from rich.console import Console

MODERN_COLOR_SYSTEM = 'truecolor'
#   what `Console.color_system` reports for a terminal that can show
#   truecolor. every other value ('standard', '256', 'windows', or `None`
#   when the output is not a terminal) falls back to the legacy palette.

Gradient = tp.Union[str, tp.Tuple[str, str]]
#   a two-stop gradient in a modern terminal, or a single color in a legacy
#   one. the renderer's `_gradient()` handles both.


class ModernPalette:
    """
    For the truecolor terminals. The colors are taken from the catppuccin
    'mocha' flavour - the name of the color is noted next to each of them.
    """

    class title:
        # the program banner, and the title of the parameters panel
        gradient = ('#fab387', '#f9e2af')  # peach -> yellow

    class panel:
        class border:
            commands = '#cba6f7'  # mauve
            parameters = '#89b4fa'  # blue

    class commands:
        # the 'FUNCTIONS' / 'COMMAND GROUPS' panel
        index = '#f9e2af'  # yellow
        name = '#cba6f7'  # mauve
        desc = '#7f849c'  # overlay1 (a gray)

    class groups:
        # the command groups tree
        name = 'bold #cba6f7'  # mauve
        guide = '#6c7086'  # overlay0
        command = '#94e2d5'  # teal
        desc = '#7f849c'  # overlay1

    class param:
        # the 'PARAMETERS' panel
        required = '#f38ba8'  # red
        index = '#f9e2af'  # yellow
        name = 'bold #89b4fa'  # blue
        short = 'bold #a6e3a1'  # green
        type = 'dim #f9e2af'  # dim yellow
        desc = '#7f849c'  # overlay1
        #   the description text, wherever it comes from: the description of
        #   the function (drawn above the panel), the description column of
        #   the parameters table, and the description line of the stacked
        #   layout. all three share this color.
        default = '#fab387'  # peach

    class logo:
        # 'powered by argsense'. the gradient echoes the border of the panel
        # it follows.
        commands = ('#cba6f7', '#f5c2e7')  # mauve -> pink
        parameters = ('#89b4fa', '#b4befe')  # blue -> lavender


class LegacyPalette:
    """
    For the terminals that can not show truecolor. Only the 16 ansi colors
    (and the styles built on them) are used. `bright_black` is the gray here:
    unlike `grey50` it is a plain ansi color, so every terminal understands
    it.
    """

    class title:
        gradient = 'yellow'

    class panel:
        class border:
            commands = 'magenta'
            parameters = 'blue'

    class commands:
        index = 'yellow'
        name = 'magenta'
        desc = 'bright_black'

    class groups:
        name = 'bold magenta'
        guide = 'dim'
        command = 'cyan'
        desc = 'bright_black'

    class param:
        required = 'red'
        index = 'yellow'
        name = 'bold blue'
        short = 'bold green'
        type = 'dim yellow'
        desc = 'bright_black'
        #   see `ModernPalette.param.desc` - the same three places.
        default = 'bright_red'

    class logo:
        commands = 'magenta'
        parameters = 'blue'


Palette = tp.Union[ModernPalette, LegacyPalette]
"""Either of the two palettes above."""


def get_palette(console: tp.Optional[Console] = None) -> Palette:
    """
    Pick the palette for the console in use.

    Note:
        Pass the console along when the caller does not print to the global
        one (for example the screenshot tooling assigns its own console to
        the renderer). Do not resolve the palette once at import time: the
        console may be replaced later, and with it the color support.
    """
    if console is None:
        console = get_console()
    if console.color_system == MODERN_COLOR_SYSTEM:
        return ModernPalette()
    return LegacyPalette()
