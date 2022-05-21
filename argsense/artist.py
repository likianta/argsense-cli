"""
where the masterpiece derived.
"""
import typing as t

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import config


def draw_title(prog_name: str,
               commands=True,
               options=True,
               arguments=t.Optional[t.Sequence[str]]) -> str:
    """
    illustration examples:
        python -m argsense <COMMANDS> [OPTIONS]
        python -m argsense [OPTIONS] <ARGUMENTS>
        python -m argsense [OPTIONS]
    """
    return '\n'.join((
        '',  # empty line
        '[b]{}[/]'.format(  # title
            ' '.join(filter(None, (
                prog_name,
                commands and f'[magenta]<COMMANDS>[/]',
                options and f'[dim]\\[OPTIONS][/]',
                arguments and '[blue]{}[/]'.format(' '.join(arguments))
            )))
        ),
        '',  # empty line
        # # '[yellow dim]{}[/]'.format(  # splitter
        # #     '─' * len(' '.join(filter(None, (
        # #         # ' ',
        # #         prog_name.replace('[bright_red]', '').replace('[/]', ''),
        # #         commands and f'<COMMANDS>',
        # #         options and f'[OPTIONS]',
        # #         arguments and f'<ARGUMENTS>',
        # #         # ' ',
        # #     ))))
        # # ),
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
    table = Table.grid(expand=True)
    table.add_column('name', style='blue')
    table.add_column('desc', style='default')
    
    for k, v in data.items():
        table.add_row(_reformat_name(k, style), v)
    
    return Panel(
        table,
        border_style=border_style,
        padding=(0, 2),
        title=f'[b]{title}[/]',
        title_align='right',
    )


def post_logo(style: t.Literal['magenta', 'blue']) -> Text:
    from rich.color import Color
    if style == 'magenta':
        color_pair = ('#ed3b3b', '#d08bf3')  # rose red -> violet
    else:
        # color_pair = ('#2d34f1', '#9294f0')  # ocean blue -> light blue
        color_pair = ('#0a87ee', '#9294f0')  # calm blue -> light blue
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


def _reformat_name(name: str, style: str) -> str:
    """
    args:
        style: literal['cmd', 'arg', 'opt', 'ext']
    
    style:
        style   text color  name form
        -----   ----------  ------------------------------
        cmd     magenta     aaa-bbb
        arg     blue        AAA-BBB
        opt     default     --aaa-bbb/--not-aaa-bbb, -m/-M
        ext     dim         --aaa-bbb, -m
    """
    name = name.replace('_', '-')
    if style == 'arg':
        name = name.upper()
    elif style in ('opt', 'ext'):
        name = '--' + name
    
    if style == 'cmd':
        return f'[magenta]{name}[/]'
    elif style == 'arg':
        return f'[blue]{name}[/]'
    elif style == 'opt':
        return f'[default]{name}[/]'
    elif style == 'ext':
        return f'[dim]{name}[/]'
