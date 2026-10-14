import math
import os
import typing as t
from random import randint

import neoprint as np
import rich.box
import rich.console
import rich.padding
import rich.panel
import rich.table
import rich.text
from rich import get_console

from .style import color
from ... import config
from ...converter import val_2_cval
from ...parser import Argv
from ...parser import FuncInfo

console = get_console()


def render_functions(argv: Argv, funcs: t.Iterable[FuncInfo]) -> None:
    console.print(
        _simple_gradient(
            _detect_program_name(argv) + ' ...',
            (0xFF0000, 0xFFFF00),  # red -> yellow
        ),
        justify='center',
        style='bold',
    )

    table = rich.table.Table.grid(expand=True, padding=(0, 4))
    table.add_column('index', style=color.yellow)
    table.add_column('function', style=color.magenta)
    table.add_column('description', style=color.gray2, ratio=1)

    for i, f in enumerate(funcs, 1):
        table.add_row(str(i), f.name, f.desc)

    console.print(
        rich.panel.Panel(
            table,
            border_style=color.magenta,
            padding=(0, 2),
            title='FUNCTIONS',
            title_align='right',
        )
    )
    if config.POST_LOGO_IN_HELP_INTERFACE:
        _post_logo(color_seed='magenta')


def render_function_parameters(
    argv: Argv, func_info: FuncInfo, *, show_func_name_in_title: bool = True
) -> None:
    has_any_args = bool(func_info.args or func_info.kwargs)

    title_parts = [_detect_program_name(argv)]
    if show_func_name_in_title:
        title_parts.append(func_info.name)
    if has_any_args:
        title_parts.append('...')
    console.print(
        _simple_gradient(
            ' '.join(title_parts),
            (0xFF0000, 0xFFFF00),  # red -> yellow
        ),
        justify='center' if has_any_args else None,
        style='bold',
    )

    if func_info.desc:
        console.print(
            rich.padding.Padding(
                rich.text.Text(func_info.desc, style=color.gray2), (0, 2, 0, 2)
            )
        )

    if not has_any_args:
        return

    rows = _collect_parameter_rows(func_info)
    plan = _make_layout_plan(rows)

    if plan['stacked']:
        table = _render_stacked_table(rows, plan['omit_default_prefix'])
    else:
        table = _render_grid_table(rows, plan['omit_default_prefix'])

    if table.rows:
        console.print(
            rich.panel.Panel(
                table,
                border_style=color.blue,
                padding=(0, 2),
                title='PARAMETERS',
                title_align='right',
            )
        )
        if config.POST_LOGO_IN_HELP_INTERFACE:
            _post_logo(color_seed='blue')


# ------------------------------------------------------------------------------
# parameters rendering


def _collect_parameter_rows(func_info: FuncInfo) -> t.List[dict]:
    """
    flatten the function's parameters into a list of row descriptors, so that
    the layout can be decided before actually rendering them.
    """
    rows: t.List[dict] = []
    has_var_args = func_info.has_var_args
    i = 0

    for arg in func_info.args0.values():
        i += 1
        name, short = _split_cname(arg['cname'])
        rows.append(
            {
                'required': '*',
                'index': '{:<4}'.format(i),
                'name': name,
                'short': short,
                'type': arg['ctype'].name,
                'desc': arg['desc'],
                'default': None,
            }
        )
    for arg in func_info.args1.values():
        i += 1
        name, short = _split_cname(arg['cname'])
        rows.append(
            {
                'required': ' ',
                'index': '{:<4}'.format(i),
                'name': name.lstrip('-'),
                'short': short,
                'type': arg['ctype'].name,
                'desc': arg['desc'],
                'default': val_2_cval(arg['default']),
            }
        )
    if func_info.args2:
        rows.append(
            {
                'required': ' ',
                'index': '*',
                'name': func_info.args2['*']['cname'],
                'short': '',
                'type': func_info.args2['*']['ctype'].name,
                'desc': '',
                'default': None,
            }
        )
    for arg in func_info.args3.values():
        i += 1
        name, short = _split_cname(arg['cname'])
        is_var_kwargs = arg['default'] is ...  # WORKAROUND
        is_required = arg['default'] == ':required'  # WORKAROUND
        rows.append(
            {
                'required': '*' if is_required else ' ',
                'index': '-   '
                if has_var_args or is_var_kwargs
                else '{:<4}'.format(i),
                'name': name.lstrip('-'),
                'short': short,
                'type': arg['ctype'].name,
                'desc': arg['desc'],
                'default': None if is_required else val_2_cval(arg['default']),
            }
        )
    if func_info.args4 and not config.HIDE_UNSTATED_VARIABLE_KWARGS:
        rows.append(
            {
                'required': ' ',
                'index': '-   ',
                'name': '...',
                'short': '',
                'type': func_info.args4['**']['ctype'].name,
                'desc': '[dim](this function may accept more keyword arguments as '
                'implicit vars...)[/]',
                'default': None,
            }
        )

    return rows


def _split_cname(cname: str) -> t.Tuple[str, str]:
    if ', ' in cname:
        return tuple(cname.split(', '))  # type: ignore
    return cname, ''


def _render_default_value(
    value: t.Optional[str], omit_default_prefix: bool, leading: str = ''
) -> str:
    if value is None:
        return ''
    return '{}{}{}'.format(
        leading, '' if omit_default_prefix else 'default = ', value
    )


# ------------------------------------------------------------------------------
# layout plan


def _get_panel_inner_width() -> int:
    """
    the inner (content) width of the 'PARAMETERS' panel. it is the console
    width minus the panel's borders and horizontal padding.
    """
    return max(
        1,
        console.width
        - 2 * config.PARAM_PANEL_BORDER_WIDTH
        - 2 * config.PARAM_PANEL_PADDING_X,
    )


def _cell_texts(row: dict, omit_default_prefix: bool) -> t.Dict[str, str]:
    """get the cell texts of a row, used for measuring the column widths."""
    return {
        'required': row['required'],
        'index': row['index'],
        'name': row['name'],
        'short': (row['short'] + '   ') if row['short'] else '   ',
        'type': row['type'] + '   ',
        'default': _render_default_value(
            row['default'], omit_default_prefix, leading='   '
        ),
    }


def _measure_columns(rows: t.List[dict], omit_default_prefix: bool) -> dict:
    keys = ('required', 'index', 'name', 'short', 'type', 'default')
    return {
        k: max(
            (len(_cell_texts(r, omit_default_prefix)[k]) for r in rows),
            default=0,
        )
        for k in keys
    }


def get_param_desc_width(rows: t.List[dict], omit_default_prefix: bool) -> int:
    """
    estimate how many characters are left for the 'param_desc' column.
    """
    widths = _measure_columns(rows, omit_default_prefix)
    fixed = sum(widths.values())
    overhead = 2 * config.PARAM_TABLE_NUM_COLUMNS  # per-cell l/r padding
    return _get_panel_inner_width() - fixed - overhead


def get_param_desc_width_ratio(
    rows: t.List[dict], omit_default_prefix: bool
) -> float:
    """
    the proportion of the 'param_desc' column's width to the whole panel. the
    smaller it is, the more cramped the description column looks.
    """
    panel_width = _get_panel_inner_width()
    desc_width = get_param_desc_width(rows, omit_default_prefix)
    return desc_width / panel_width


def is_param_desc_width_too_narrow(
    rows: t.List[dict], omit_default_prefix: bool = False
) -> bool:
    """
    judge whether the 'param_desc' column is too narrow (its width takes up too
    little proportion of the whole panel).
    """
    return (
        get_param_desc_width_ratio(rows, omit_default_prefix)
        < config.LEAST_WIDTH_RATIO_OF_PARAM_DESC
    )


def _make_layout_plan(rows: t.List[dict]) -> t.Dict[str, bool]:
    """
    decide the parameters table layout:
        1. if the description column is wide enough, keep the single-line grid.
        2. if it is too narrow, stack the description onto a second line so
           that it can use the full panel width.
        3. optionally (see `config.OMIT_DEFAULT_PREFIX_IF_DESC_TOO_NARROW`),
           try to omit the "default = " prefix first to reclaim some space, and
           only stack when that is still not enough.
    """
    if not any(row['desc'] for row in rows):
        # there is nothing to describe, keep the original single-line grid.
        return {'omit_default_prefix': False, 'stacked': False}
    if not is_param_desc_width_too_narrow(rows):
        return {'omit_default_prefix': False, 'stacked': False}
    if config.OMIT_DEFAULT_PREFIX_IF_DESC_TOO_NARROW:
        if not is_param_desc_width_too_narrow(rows, omit_default_prefix=True):
            return {'omit_default_prefix': True, 'stacked': False}
        return {'omit_default_prefix': True, 'stacked': True}
    return {'omit_default_prefix': False, 'stacked': True}


# ------------------------------------------------------------------------------
# renderers for the two layouts


def _render_grid_table(
    rows: t.List[dict], omit_default_prefix: bool
) -> rich.table.Table:
    table = rich.table.Table.grid(expand=True, padding=(0, 1))
    #   padding=(0, 1): cell's padding, (vertical, horizontal).
    #       we use small padding for horizontal, so that the required mark -
    #       '*' can be closer to the param name.
    #       but other fields should have more padding, the workaround is -
    #       to use `value + '   '` to manually add the spaces.
    #   expand=True:
    #       set expand to True, so that columns can use `ratio` to decide -
    #       their widths. currently we only set `desc` column to be -
    #       expanded.
    table.add_column('required', style=color.red)
    table.add_column('index', style=color.yellow)
    table.add_column('param', style=color.blue + ' bold')
    table.add_column('short', style=color.green + ' bold')
    table.add_column('type', style='dim')
    table.add_column('description', style=None, ratio=1)
    table.add_column('default', style=color.scarlet)

    for row in rows:
        cells = _cell_texts(row, omit_default_prefix)
        table.add_row(
            cells['required'],
            cells['index'],
            cells['name'],
            cells['short'],
            cells['type'],
            row['desc'],
            cells['default'],
        )
    return table


def _render_stacked_table(
    rows: t.List[dict], omit_default_prefix: bool
) -> rich.table.Table:
    """
    in this layout, each parameter takes two (or more) lines:
        line 1:  index; param_name; param_type; (spaces); default_value
        line 2+: (indent) param_desc
    this gives the description the full panel width.
    """
    panel_width = _get_panel_inner_width()
    w_index = max((len(r['index']) for r in rows), default=0)
    w_name = max((len(r['name']) for r in rows), default=0)
    w_short = max((len(r['short']) for r in rows), default=0)
    w_type = max((len(r['type']) for r in rows), default=0)
    indent = 1 + 1 + w_index + 1  # required + space + index + space

    table = rich.table.Table.grid(expand=True, padding=(0, 0))
    table.add_column('body', ratio=1)

    prev_has_desc = False
    for i, row in enumerate(rows):
        if i > 0 and prev_has_desc:
            table.add_row('')  # a blank line after a described parameter
        table.add_row(
            _build_stacked_block(
                row,
                panel_width,
                indent,
                w_index,
                w_name,
                w_short,
                w_type,
                omit_default_prefix,
            )
        )
        prev_has_desc = bool(row['desc'])
    return table


def _build_stacked_block(
    row: dict,
    panel_width: int,
    indent: int,
    w_index: int,
    w_name: int,
    w_short: int,
    w_type: int,
    omit_default_prefix: bool,
) -> rich.console.Group:
    head = rich.text.Text()
    head.append(row['required'], style=color.red)
    head.append(' ')
    head.append(row['index'].ljust(w_index), style=color.yellow)
    head.append(' ')
    head.append(row['name'].ljust(w_name), style=color.blue + ' bold')
    head.append(' ')
    head.append(row['short'].ljust(w_short), style=color.green + ' bold')
    head.append(' ')
    head.append(row['type'].ljust(w_type), style='dim')

    default_value = _render_default_value(row['default'], omit_default_prefix)
    if default_value:
        gap = panel_width - len(head) - len(default_value)
        head.append(' ' * max(2, gap))
        head.append(default_value, style=color.scarlet)

    if row['desc']:
        return rich.console.Group(
            head,
            rich.padding.Padding(
                rich.text.Text(row['desc'], style=color.gray2),
                (0, 0, 0, indent),
            ),
        )
    else:
        return rich.console.Group(head)


def _detect_program_name(argv: Argv) -> str:
    """
    code reference:
        `[third_lib] click : [path] /utils.py : [def] _detect_program_name()`
    """
    parts = []

    if argv.launcher[0].endswith(
        ('py', 'py.exe', 'python', 'python.exe', 'python3')
    ):
        parts.append(
            'python'
            if config.PROGRAM_NAME_STYLE == 'fixed'
            else 'py'
            if os.name == 'nt'
            else 'python3'
        )
        if len(argv.launcher) > 1:
            assert len(argv.launcher) == 2 and argv.launcher[1] == '-m'
            parts.append('-m')
    else:
        parts.extend(argv.launcher)

    if parts[-1] == '-m':
        parts.append(argv.target[0])
    else:
        parts.append(os.path.basename(argv.target[0]))

    # if argv.possible_function:
    #     parts.append(argv.possible_function)

    return ' '.join(parts)


# FIXME
def _gradient(text: str, colors: t.Sequence[int]):
    if len(colors) == 2:
        return _simple_gradient(text, colors)  # noqa
    else:
        text_parts = []
        substr_len = math.ceil(len(text) / len(colors))
        for i in range(len(colors) - 1):
            text_parts.append(
                _simple_gradient(
                    text[(i * substr_len) : ((i + 1) * substr_len)],
                    (colors[i], colors[i + 1]),
                )
            )
        return rich.text.Text.assemble(*text_parts)


def _post_logo(color_seed: str = 'white') -> None:
    console.print(
        _simple_gradient(
            '🔥 powered by argsense',
            (0x0A87EE, 0x9294F0)
            if color_seed == 'blue'
            else (0xF38CFD, 0xCE628C)
            if color_seed == 'magenta'
            else (0xF47FA4, 0xF49364)
            if color_seed == 'tan'
            else (0xFFFFFF, 0x909090)
            if color_seed == 'white'
            else _roll_color_pair(),
        ),
        justify='right',
        style='bold',
        end=' \n',
    )


def _roll_color_pair() -> t.Tuple[int, int]:
    start = int(
        '{:02x}{:02x}{:02x}'.format(
            randint(128, 255), randint(128, 255), randint(128, 255)
        ),
        16,
    )
    end = int(
        '{:02x}{:02x}{:02x}'.format(
            randint(0, 127), randint(0, 127), randint(0, 127)
        ),
        16,
    )
    np.show(
        ':r',
        '[#{:06x}]#{:06x}[/] -> [#{:06x}]#{:06x}[/]'.format(
            start, start, end, end
        ),
    )
    return start, end


def _simple_gradient(text: str, colors: t.Tuple[int, int]) -> rich.text.Text:
    color1, color2 = colors
    # np.show('{:06X}, {:06X}'.format(color1, color2), ':pv')
    rich_text = rich.text.Text(text, style='bold')
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
    dr = r2 - r1
    dg = g2 - g1
    db = b2 - b1
    size = len(rich_text)
    for index in range(size):
        blend = index / size
        color = '#{}{}{}'.format(
            f'{int(r1 + dr * blend):02X}',
            f'{int(g1 + dg * blend):02X}',
            f'{int(b1 + db * blend):02X}',
        )
        rich_text.stylize(color, index, index + 1)
    return rich_text
