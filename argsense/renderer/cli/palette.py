"""
The color tables used by the rich renderer.

Three palettes are maintained, and `get_palette()` picks one for the console
in use:

    ModernPalette
        For the terminals that report the truecolor color system. The colors
        are the 'mocha' flavour of the catppuccin palette
        (https://catppuccin.com/palette), and the titles are drawn as a
        gradient.

    ModernFlatPalette
        For the terminals that report the 256-color color system. It keeps
        the same catppuccin colors, but it drops the gradients: the xterm
        color cube has only six levels per channel, so a ramp is reduced to a
        few flat bands.

    LegacyPalette
        For the terminals that only know the 16 ansi colors - this is what
        `standard` and the legacy windows console report - and for the runs
        that get no color at all (`color_system` is `None` when the output is
        not a terminal).

The detection is delegated to rich, which already knows whether the console
is the legacy windows one (see `rich.console.detect_legacy_windows`) and
which color system it supports (see `rich.console.Console.color_system`). A
legacy windows console is reported as `ColorSystem.WINDOWS`, so it never
looks like a truecolor one.

Note that picking a palette is only about colors: when the console can not
show them at all, rich drops every escape sequence before it writes anything
(see `rich.style.Style.render`).
"""

import typing as tp

from rich import get_console
from rich.console import Console

MODERN_COLOR_SYSTEMS = ('truecolor', '256')
#   the values of `Console.color_system` that get the modern colors.

GRADIENT_COLOR_SYSTEM = 'truecolor'
#   among them, the one that can also blend two colors into a ramp. that is
#   why `ModernFlatPalette` is used for the rest of them.

Gradient = tp.Union[str, tp.Tuple[str, str]]
#   a two-stop gradient, or a single color when the console can not blend.
#   the renderer's `_gradient()` handles both.


class ModernPalette:
    """
    For the terminals that report the truecolor color system.

    The colors are taken from the catppuccin 'mocha' flavour - the name of
    the color is noted next to each of them - and the titles are drawn as a
    gradient.
    """

    class title:
        # the program banner, and the title of the parameters panel
        # gradient = ('#f38ba8', '#f9e2af')  # red -> yellow
        gradient = ('#ff0000', '#ffff00')  # custom-red -> custom-yellow

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
        default = '#f38ba8'  # red

    class logo:
        # 'powered by argsense'. the gradient echoes the border of the panel
        # it follows.
        commands = ('#cba6f7', '#c4364a')  # mauve -> custom-dark-red
        parameters = ('#89b4fa', '#7f849c')  # blue -> overlay1


class ModernFlatPalette(ModernPalette):
    """
    For the terminals that report the 256-color color system.

    It keeps the modern colors, but it can not use the gradients: the xterm
    color cube has only six levels per channel, so a ramp is reduced to six
    flat bands. The single colors below stand in for them.
    """

    class title:
        gradient = '#f38ba8'  # red

    class logo:
        #   the first stop of each gradient of `ModernPalette`, that is, the
        #   color that echoes the border of the panel it follows.
        commands = '#cba6f7'  # mauve
        parameters = '#89b4fa'  # blue


class LegacyPalette:
    """
    For the terminals that only know the 16 ansi colors, and for the runs
    that get no color at all.

    Only the ansi color names (and the styles built on them) are used.
    `bright_black` is the gray here: unlike `grey50` it is a plain ansi
    color, so every terminal understands it.
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
"""Either of the palettes above. `ModernFlatPalette` is one of them."""


def get_palette(console: tp.Optional[Console] = None) -> Palette:
    """
    Pick the palette for the console in use: `ModernPalette` on a truecolor
    terminal, `ModernFlatPalette` on a 256-color one, `LegacyPalette`
    otherwise.

    Note:
        Pass the console along when the caller does not print to the global
        one (for example the screenshot tooling assigns its own console to
        the renderer). Do not resolve the palette once at import time: the
        console may be replaced later, and with it the color support.
    """
    if console is None:
        console = get_console()
    color_system = console.color_system
    if color_system not in MODERN_COLOR_SYSTEMS:
        return LegacyPalette()
    if color_system == GRADIENT_COLOR_SYSTEM:
        return ModernPalette()
    return ModernFlatPalette()
