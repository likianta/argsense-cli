import os
import typing as t

import rich.box
import rich.color
import rich.console
import rich.padding
import rich.panel
import rich.table
import rich.text
import rich.tree
from rich import get_console

from .palette import get_palette
from .palette import Gradient
from .palette import Palette
from ... import config
from ...converter import val_2_cval
from ...parser import Argv
from ...parser import FuncInfo

console = get_console()


def _palette() -> Palette:
    """
    The color table to draw with.

    It is looked up on every call instead of once at import time, because the
    console may still be replaced later (the screenshot tooling does that to
    record a truecolor console), and the palette depends on it.
    """
    return get_palette(console)


def render_functions(
    argv: Argv,
    funcs: t.Iterable[FuncInfo],
    groups: t.Optional[t.Sequence[t.Tuple[str, t.Sequence[str]]]] = None,
) -> None:
    """
    Render the command list.

    params:
        groups:
            the group structure built by `cli.run_group(...)`. When it is
            given, the commands are shown as a tree grouped by their group
            names; otherwise they are shown as a flat table (this is what
            `cli.run(...)` does).
    """
    palette = _palette()
    console.print(
        _gradient(_detect_program_name(argv) + ' ...', palette.title.gradient),
        justify='center',
        style='bold',
    )

    funcs = list(funcs)
    if groups:
        content = _build_command_groups(funcs, groups, palette)
        title = 'COMMAND GROUPS'
    else:
        content = _build_func_table(funcs, palette)
        title = 'FUNCTIONS'

    console.print(
        rich.panel.Panel(
            content,
            border_style=palette.panel.border.commands,
            padding=(0, 2),
            title=title,
            title_align='right',
        )
    )
    if config.POST_LOGO_IN_HELP_INTERFACE:
        _post_logo(palette.logo.commands)


def _build_func_table(
    funcs: t.List[FuncInfo], palette: Palette
) -> rich.table.Table:
    table = rich.table.Table.grid(expand=True, padding=(0, 4))
    table.add_column('index', style=palette.commands.index)
    table.add_column('function', style=palette.commands.name)
    table.add_column('description', style=palette.commands.desc, ratio=1)

    for i, f in enumerate(funcs, 1):
        table.add_row(str(i), f.name, f.desc)

    return table


# the tree guides used by the command groups help interface. the branches are
# rounded, borrowed from `rich.box.ROUNDED`.
_TREE_GUIDE_H = rich.box.ROUNDED.row_horizontal
_TREE_GUIDE_FORK = rich.box.ROUNDED.row_left
_TREE_GUIDE_LAST = rich.box.ROUNDED.bottom_left


class _GroupTree(rich.tree.Tree):
    """
    The tree used by the command groups help interface. Its branches take the
    rounded corners of `rich.box.ROUNDED`, so the last command of a group is
    drawn as "╰──" instead of "└──".
    """

    TREE_GUIDES = [
        (
            '    ',
            ' │  ',
            ' {}{} '.format(_TREE_GUIDE_FORK, _TREE_GUIDE_H),
            ' {}{} '.format(_TREE_GUIDE_LAST, _TREE_GUIDE_H),
        ),
        *rich.tree.Tree.TREE_GUIDES[1:],
    ]


def _build_command_groups(
    funcs: t.List[FuncInfo],
    groups: t.Sequence[t.Tuple[str, t.Sequence[str]]],
    palette: Palette,
) -> rich.console.Group:
    """
    Build the tree-like command list used by `cli.run_group(...)`.
    """
    lookup = {f.name: f for f in funcs}
    name_width = max((len(x) for x in lookup), default=0)

    blocks: t.List[t.Any] = []
    used: t.Set[str] = set()

    for group_name, cmd_names in groups:
        names = [x for x in cmd_names if x in lookup]
        if not names:
            continue
        used.update(names)

        if blocks:
            blocks.append('')
        tree = _GroupTree(
            rich.text.Text(group_name, style=palette.groups.name),
            guide_style=palette.groups.guide,
        )
        for name in names:
            tree.add(_build_command_leaf(lookup[name], name_width, palette))
        blocks.append(tree)

    # commands that do not belong to any group (e.g. they were registered by
    # `@cli` before `cli.run_group(...)` was called) are still listed.
    leftovers = [f for f in funcs if f.name not in used]
    if leftovers:
        if blocks:
            blocks.append('')
        tree = _GroupTree(
            rich.text.Text(' ungrouped', style=palette.groups.name),
            guide_style=palette.groups.guide,
        )
        for f in leftovers:
            tree.add(_build_command_leaf(f, name_width, palette))
        blocks.append(tree)

    return rich.console.Group(*blocks)


def _build_command_leaf(
    func_info: FuncInfo, name_width: int, palette: Palette
) -> rich.text.Text:
    """
    One command of a group: its name, padded so that the descriptions of all
    groups line up, followed by its description.
    """
    line = rich.text.Text()
    line.append(func_info.name.ljust(name_width), style=palette.groups.command)
    line.append('  ')
    line.append_text(
        _render_text(
            func_info.desc, palette.groups.desc, _resolve_markup(func_info)
        )
    )
    return line


def render_function_parameters(
    argv: Argv, func_info: FuncInfo, *, show_func_name_in_title: bool = True
) -> None:
    palette = _palette()
    has_any_args = bool(func_info.args or func_info.kwargs)
    use_markup = _resolve_markup(func_info)

    title_parts = [_detect_program_name(argv)]
    if show_func_name_in_title:
        title_parts.append(func_info.name)
    if has_any_args:
        title_parts.append('...')
    console.print(
        _gradient(' '.join(title_parts), palette.title.gradient),
        justify='center' if has_any_args else None,
        style='bold',
    )

    if func_info.desc:
        console.print(
            rich.padding.Padding(
                _render_text(func_info.desc, palette.param.desc, use_markup),
                (0, 2, 0, 2),
            )
        )

    if not has_any_args:
        return

    rows = _collect_parameter_rows(func_info)
    plan = _make_layout_plan(rows)

    if plan['stacked']:
        table = _render_stacked_table(
            rows, plan['omit_default_prefix'], use_markup, palette
        )
    else:
        table = _render_grid_table(
            rows, plan['omit_default_prefix'], use_markup, palette
        )

    if table.rows:
        console.print(
            rich.panel.Panel(
                table,
                border_style=palette.panel.border.parameters,
                padding=(0, 2),
                title='PARAMETERS',
                title_align='right',
            )
        )
        if config.POST_LOGO_IN_HELP_INTERFACE:
            _post_logo(palette.logo.parameters)


def _resolve_markup(func_info: FuncInfo) -> bool:
    """
    a per-command `rich` setting (`@cli.cmd(rich=...)`) takes precedence over
    the global `config.USE_RICH_MARKUP`.
    """
    if func_info.use_rich_markup is None:
        return config.USE_RICH_MARKUP
    return func_info.use_rich_markup


def _render_text(
    text: str, style: t.Optional[str], use_markup: bool
) -> rich.text.Text:
    """
    build a rich text object. when `use_markup` is false, the text is treated
    literally, so that bracketed text (e.g. "[2024-01-01]") is shown as-is,
    instead of being parsed (and possibly rejected) as rich markup.
    """
    if use_markup:
        return rich.text.Text.from_markup(text, style=style)
    return rich.text.Text(text, style=style)


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
                'desc': '(this function may accept more keyword arguments as '
                'implicit vars...)',
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
    rows: t.List[dict],
    omit_default_prefix: bool,
    use_markup: bool,
    palette: Palette,
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
    table.add_column('required', style=palette.param.required)
    table.add_column('index', style=palette.param.index)
    table.add_column('param', style=palette.param.name)
    table.add_column('short', style=palette.param.short)
    table.add_column('type', style=palette.param.type)
    table.add_column('description', style=palette.param.desc, ratio=1)
    table.add_column('default', style=palette.param.default)

    for row in rows:
        cells = _cell_texts(row, omit_default_prefix)
        table.add_row(
            cells['required'],
            cells['index'],
            cells['name'],
            cells['short'],
            cells['type'],
            _render_text(row['desc'], None, use_markup),
            cells['default'],
        )
    return table


def _render_stacked_table(
    rows: t.List[dict],
    omit_default_prefix: bool,
    use_markup: bool,
    palette: Palette,
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
                use_markup,
                palette,
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
    use_markup: bool,
    palette: Palette,
) -> rich.console.Group:
    head = rich.text.Text()
    head.append(row['required'], style=palette.param.required)
    head.append(' ')
    head.append(row['index'].ljust(w_index), style=palette.param.index)
    head.append(' ')
    head.append(row['name'].ljust(w_name), style=palette.param.name)
    head.append(' ')
    head.append(row['short'].ljust(w_short), style=palette.param.short)
    head.append(' ')
    head.append(row['type'].ljust(w_type), style=palette.param.type)

    default_value = _render_default_value(row['default'], omit_default_prefix)
    if default_value:
        gap = panel_width - len(head) - len(default_value)
        head.append(' ' * max(2, gap))
        head.append(default_value, style=palette.param.default)

    if row['desc']:
        return rich.console.Group(
            head,
            rich.padding.Padding(
                _render_text(row['desc'], palette.param.desc, use_markup),
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


def _gradient(text: str, gradient: Gradient) -> rich.text.Text:
    """
    Draw a title in its gradient.

    A legacy palette hands a single color instead of a pair, because such a
    terminal can not blend two colors into a readable ramp. The text is then
    drawn flat, in that color.
    """
    if isinstance(gradient, str):
        return rich.text.Text(text, style='bold ' + gradient)

    start, end = gradient
    r1, g1, b1 = rich.color.Color.parse(start).get_truecolor()
    r2, g2, b2 = rich.color.Color.parse(end).get_truecolor()
    rich_text = rich.text.Text(text, style='bold')
    size = len(rich_text)
    for index in range(size):
        blend = index / size
        rich_text.stylize(
            '#{:02X}{:02X}{:02X}'.format(
                int(r1 + (r2 - r1) * blend),
                int(g1 + (g2 - g1) * blend),
                int(b1 + (b2 - b1) * blend),
            ),
            index,
            index + 1,
        )
    return rich_text


def _post_logo(gradient: Gradient) -> None:
    console.print(
        _gradient('🔥 powered by argsense', gradient),
        justify='right',
        style='bold',
        end=' \n',
    )
