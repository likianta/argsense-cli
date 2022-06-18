"""
where the masterpiece derived.
"""
import typing as t

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .style import palette


class T:
    class Title:
        Command = t.Optional[str]
        Options = t.Optional[str]
        Arguments = t.Optional[t.Sequence[str]]
        # Align = t.Literal['left', 'center']
    
    # Style = t.Literal['grp', 'cmd', 'arg', 'opt', 'ext']
    PanelData = t.Iterable[t.Tuple[str, ...]]


def draw_title(prog_name: str,
               command: T.Title.Command = '<COMMAND>',
               options: T.Title.Options = '[OPTIONS]',
               arguments: T.Title.Arguments = None,
               serif_line=False) -> str:
    """
    illustration examples:
        python -m argsense <COMMAND> [OPTIONS]
        python -m argsense [OPTIONS] <ARGUMENTS>
        python -m argsense [OPTIONS]
    """
    
    def render_prog_name():
        # reference: [./cli.py : def _detect_program_name()]
        
        color = palette.title.prog_name
        
        if prog_name.endswith('.exe'):
            return '[{fg}]{fname}[/]'.format(
                fg=color.exe, fname=prog_name
            )
        else:
            if ' -m ' in prog_name:
                p, m, t = prog_name.split(' ', 2)
                return (
                    '[{fg1}]{python}[/] '
                    '[{fg2}]-m[/] '
                    '[{fg3}]{pyfile}[/]'.format(
                        python=p,
                        pyfile=t,
                        fg1=color.python,
                        fg2=color.m,
                        fg3=color.py,
                    ))
            else:
                p, t = prog_name.split(' ', 1)
                return '[{fg1}]{python}[/] [{fg2}]{fname}[/]'.format(
                    python=p,
                    fname=t,
                    fg1=color.python,
                    fg2=color.py,
                )
    
    def render_command():
        tmpl = f'[{palette.title.command}]{{}}[/]'
        return tmpl.format(command)
    
    def render_options():
        if options:
            tmpl = f'[{palette.title.option}]{{}}[/]'
            if '[' in options:
                return tmpl.format(options.replace('[', '\\['))
            else:
                return tmpl.format(options)
        else:
            return ''
    
    def render_arguments() -> str:
        # experimental: if the length of arguments is longer than 3, use
        # stagger color (light-blue and dark-blue) to improve readability.
        if arguments:
            if len(arguments) >= 3:
                return ' '.join(
                    '[{fg}]{text}[/]'.format(
                        fg=palette.title.argument1 if i % 2 == 0
                        else palette.title.argument2,
                        text=x
                    ) for i, x in enumerate(arguments)
                )
            return '[{}]{}[/]'.format(
                palette.title.argument1, ' '.join(arguments)
            )
        else:
            return ''
    
    return '\n'.join((
        '',  # empty line
        '[b]{}[/]'.format(  # title
            ' '.join(filter(None, (
                render_prog_name(),
                render_command(),
                render_options(),
                render_arguments(),
            )))
        ),
        '' if not serif_line else (
            '[dim]{}[/]'.format(  # splitter
                # note: '─' for solid line, or '-' for dotted line.
                '─' * len(' '.join(filter(None, (
                    prog_name, command, options,
                    arguments and ' '.join(arguments),
                ))))
            )
        )
    ))


def draw_commands_panel(commands: T.PanelData) -> Panel:
    return _draw_panel(
        fields=('name', 'desc'),
        data=commands,
        title='COMMANDS',
        border_style=palette.panel.border.group,
    )


def draw_arguments_panel(arguments: T.PanelData) -> Panel:
    return _draw_panel(
        fields=('name', 'type', 'desc'),
        data=arguments,
        title='ARGUMENTS',
        border_style=palette.panel.border.argument,
    )


def draw_options_panel(options: T.PanelData) -> Panel:
    return _draw_panel(
        fields=('name', 'type', 'desc', 'default'),
        data=options,
        title='OPTIONS',
        border_style=palette.panel.border.option,
    )


def draw_extensions_panel(extensions: T.PanelData) -> Panel:
    return _draw_panel(
        fields=('name', 'type', 'desc', 'default'),
        data=extensions,
        title='OPTIONS [dim](EXT)[/]',
        border_style=palette.panel.border.extension,
    )


def _draw_panel(
        fields: t.Sequence[str],
        data: T.PanelData,
        title: str,
        border_style: str
) -> Panel:
    def tint_field(field: str) -> str:
        style = {
            'name'   : border_style,
            'type'   : 'yellow',
            'desc'   : 'default',
            'default': 'dim',
        }
        return style[field]
    
    from . import config
    table = Table.grid(expand=False, padding=(0, 4))
    for i, field in enumerate(fields):
        if field == 'name' and \
                (w := config.Dynamic.PREFERRED_FIELD_WIDTH_OF_NAME):
            width = w
        elif field == 'type' and \
                (w := config.Dynamic.PREFERRED_FIELD_WIDTH_OF_TYPE):
            width = w
        else:
            width = None
        table.add_column(field, style=tint_field(field), width=width)
    for row in data:
        table.add_row(*map(str, row))
    
    return Panel(
        table,
        border_style=border_style,
        padding=(0, 2),
        title=f'[b]{title}[/]',
        title_align='right',
    )


def post_logo(style: t.Literal[
    'group', 'command', 'argument', 'option'
]) -> Text:
    """ show logo in gradient color. """
    from rich.color import Color
    color_pair: tuple = getattr(palette.logo, style)
    return _blend_text(
        '♥ powered by argsense',  # TODO: embed a homepage link to the name.
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
