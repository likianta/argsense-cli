"""
where the masterpiece derived.
"""
import typing as t

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import config
from .style.color_scheme import DefaultColor as Color


def draw_title(prog_name: str,
               commands=True,
               options=True,
               arguments=t.Optional[t.Sequence[str]],
               serif_line=False) -> str:
    """
    illustration examples:
        python -m argsense <COMMANDS> [OPTIONS]
        python -m argsense [OPTIONS] <ARGUMENTS>
        python -m argsense [OPTIONS]
    """
    
    def render_prog_name():
        # style: dark-red on dim
        if prog_name.startswith('python '):
            return 'python ' + _round_wrap(
                '[{fg}]{text}[/]'.format(
                    fg=Color.scarlet,
                    # bg=Color.dim_acrylic,
                    text=prog_name[7:],
                )
            )
        else:
            return _round_wrap(
                '[{fg}]{text}[/]'.format(
                    fg=Color.scarlet,
                    # bg=Color.dim_acrylic,
                    text=prog_name
                )
            )
    
    def render_commands():
        tmpl = _round_wrap(f'[{Color.magenta}]{{}}[/]')
        if commands:
            return tmpl.format('<COMMAND>')
        else:
            return ''
    
    def render_options():
        tmpl = _round_wrap(f'[dim]{{}}[/]')
        if options:
            return tmpl.format('\\[OPTIONS]')
        else:
            return ''
    
    def render_arguments() -> str:
        if arguments:
            return '[blue]{}[/]'.format(' '.join(arguments))
        else:
            return ''
    
    return '\n'.join((
        '',  # empty line
        '[b]{}[/]'.format(  # title
            # Color.dim_acrylic,
            ' '.join(filter(None, (
                render_prog_name(),
                render_commands(),
                render_options(),
                render_arguments(),
            )))
        ),
        '' if not serif_line else (
            '[blue dim]{}[/]'.format(  # splitter
                '─' * len(' '.join(filter(None, (
                    # ' ',
                    prog_name.replace('[green]', '').replace('[/]', ''),
                    #   ~.replace(...): keep this sync with `cli.py :
                    #   _detect_program_name()`
                    commands and f'<COMMANDS>',
                    options and f'[OPTIONS]',
                    arguments and ' '.join(arguments),
                    # ' ',
                ))))
            )
        )
    ))


def draw_commands_panel(commands: dict):
    return _draw_panel(
        commands,
        title='COMMANDS',
        style='cmd',
        border_style=config.CMD_BORDER_STYLE,
    )


def draw_arguments_panel(arguments: dict):
    return _draw_panel(
        arguments,
        title='ARGUMENTS',
        style='arg',
        border_style=config.ARG_BORDER_STYLE,
    )


def draw_options_panel(options: dict):
    return _draw_panel(
        options,
        title='OPTIONS',
        style='opt',
        border_style=config.OPT_BORDER_STYLE,
    )


def draw_extensions_panel(extensions: dict):
    return _draw_panel(
        extensions,
        title='OPTIONS [dim](EX)[/]',
        style='ext',
        border_style=config.EXT_BORDER_STYLE,
    )


def _draw_panel(data: dict, title: str, style: str, border_style: str):
    table = Table.grid(expand=False, padding=(0, 4))
    table.add_column('name', style='blue')
    table.add_column('desc', style='default')
    
    def tint_name(name: str, style) -> str:
        palette = {
            'cmd': 'magenta',
            'arg': 'blue',
            'opt': 'grey74',
            'ext': 'dim',
        }
        return '[{}]{}[/]'.format(palette[style], name)
    
    for k, v in data.items():
        table.add_row(tint_name(k, style), v)
    
    return Panel(
        table,
        border_style=border_style,
        padding=(0, 2),
        title=f'[b]{title}[/]',
        title_align='right',
    )


def post_logo(style: t.Literal['blue', 'magenta', 'tan', 'white']) -> Text:
    """ show logo in gradient color. """
    from .style.color_scheme import DefaultGradient
    from rich.color import Color
    color_pair: tuple = getattr(DefaultGradient, style)
    return _blend_text(
        '♥ powered by argsense',
        *(Color.parse(x).triplet for x in color_pair)
    )


# -----------------------------------------------------------------------------
# neutral functions

def _blend_text(
        message: str,
        color1: t.Tuple[int, int, int],
        color2: t.Tuple[int, int, int]
) -> Text:
    """ blend text from one color to another.

    source: ~/rich_cli/__main__.py : blend_text()
    """
    text = Text(message)
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    dr = r2 - r1
    dg = g2 - g1
    db = b2 - b1
    size = len(text)
    for index in range(size):
        blend = index / size
        color = '#{}{}{}'.format(
            f'{int(r1 + dr * blend):02X}',
            f'{int(g1 + dg * blend):02X}',
            f'{int(b1 + db * blend):02X}'
        )
        text.stylize(color, index, index + 1)
    return text


# noinspection PyUnusedLocal
def _round_wrap(text: str, color=Color.dim_acrylic) -> str:
    """
    warning: this requires nerd fonts.
    """
    return text
    # return '{space}{text}{space}'.format(
    #     space=f'[default on {color}] [/]',
    #     text=text
    # )
    # TODO: not ready for production.
    # # return '{leading_diamon}{text}{trailing_diamond}'.format(
    # #     leading_diamon=f'[{color}]\ue0b6[/]',
    # #     text=text,
    # #     trailing_diamond=f'[{color}]\ue0b4[/]',
    # # )
