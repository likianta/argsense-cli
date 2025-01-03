import math
import os
import sys
import typing as t
from random import randint

import rich.box
import rich.padding
import rich.panel
import rich.table
import rich.text
from rich import get_console

from .style import color
from ... import config
from ...converter import val_2_cval
from ...parser import FuncInfo
from ...parser import argv_info

console = get_console()


def render_functions(funcs: t.Iterable[FuncInfo]) -> None:
    console.print(
        _simple_gradient(
            _detect_program_name() + ' ...',
            (0xFF0000, 0xFFFF00)  # red -> yellow
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
    
    _post_logo(color_seed='magenta')


def render_function_parameters(
    func_info: FuncInfo,
    *,
    show_func_name_in_title: bool = True,
) -> None:
    has_any_args = bool(func_info.args or func_info.kwargs)
    has_var_args = '*' in func_info.args
    has_var_kwargs = '**' in func_info.kwargs
    
    title_parts = [_detect_program_name()]
    if show_func_name_in_title:
        title_parts.append(func_info.name)
    if has_any_args:
        title_parts.append('...')
    console.print(
        _simple_gradient(
            ' '.join(title_parts),
            (0xFF0000, 0xFFFF00)  # red -> yellow
        ),
        justify='center' if has_any_args else None,
        style='bold',
    )
    
    if func_info.desc:
        console.print(
            rich.padding.Padding(
                rich.text.Text(func_info.desc, style=color.gray2),
                (0, 2, 0, 2)
            )
        )
    
    if not has_any_args:
        return

    # _longest_length_of_cname = max(
    #     (
    #         *(
    #             len(x['cname'].split(',')[0])
    #             for x in func_info.args.values()
    #         ),
    #         *(
    #             len(x['cname'].lstrip('-').split(',')[0])
    #             for x in func_info.kwargs.values()
    #         ),
    #     )
    # )
    #
    # def pretty_cname(cname):
    #     return '{:>{}}'.format(
    #         cname, _longest_length_of_cname
    #     )
    
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
    
    i = 0
    for key, arg in func_info.args.items():
        if key == '*':
            continue
        i += 1
        name, short = (
            arg['cname'].split(', ') if ', ' in arg['cname']
            else (arg['cname'], '')
        )
        # name = pretty_cname(name)
        table.add_row(
            '*',
            '{:<4}'.format(i),
            name,
            short + '   ',
            arg['ctype'].name + '   ',
            arg['desc'],
        )
    if has_var_args:
        table.add_row(
            ' ',
            '*',
            func_info.args['*']['cname'],
            # pretty_cname(func_info.args['*']['cname']),
            '',
            func_info.args['*']['ctype'].name + '   ',
            # '(allow passing variable arguments...)',
        )
    for key, arg in func_info.kwargs.items():
        if key == '**':
            continue
        i += 1
        name, short = (
            arg['cname'].split(', ') if ', ' in arg['cname']
            else (arg['cname'], '')
        )
        name = name.lstrip('-')  # FIXME: is this good?
        # name = pretty_cname(name)
        is_var_kwargs = arg['default'] is ...  # WORKAROUND
        table.add_row(
            ' ',
            '-   ' if has_var_args or is_var_kwargs else '{:<4}'.format(i),
            name,
            short + '   ',
            arg['ctype'].name + '   ',
            arg['desc'],
            '   ' + 'default = {}'.format(val_2_cval(arg['default'])),
        )
    if has_var_kwargs:
        table.add_row(
            ' ',
            '-   ',
            func_info.kwargs['**']['cname'],
            # pretty_cname(func_info.kwargs['**']['cname']),
            '',
            func_info.kwargs['**']['ctype'].name + '   ',
            # '(allow passing variable keyword arguments...)',
        )
    console.print(
        rich.panel.Panel(
            table,
            border_style=color.blue,
            padding=(0, 2),
            title='PARAMETERS',
            title_align='right',
        )
    )
    
    _post_logo(color_seed='blue')


def _detect_program_name(func_cname: str = None) -> str:
    """
    code reference: `lib click : /utils.py : def _detect_program_name()`
    
    returns e.g.:
        - 'python example.py'
        - 'python -m example'
        - 'python3 example.py'
        - 'python3 -m example'
        - 'example.exe'
    """
    argv = argv_info.argv + [''] * 10
    #                     ~~~~~~~~~~~ in case of IndexError
    
    parts = []  # noqa
    
    parts.append(
        'python' if config.TITLE_HEAD_STYLE == 'fixed' else
        'python' if os.name == 'nt' else
        'python3'
    )
    
    if argv[1] == '-m':
        parts.append(argv[1])
        parts.append(argv[2])
        if func_cname and argv[3] == func_cname:
            parts.append(func_cname)
    else:
        parts.append(os.path.basename(argv[1]))
        if func_cname and argv[2] == func_cname:
            parts.append(func_cname)
    
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
                    text[(i * substr_len):((i + 1) * substr_len)],
                    (colors[i], colors[i + 1])
                )
            )
        return rich.text.Text.assemble(*text_parts)


def _post_logo(color_seed: str = 'white') -> None:
    console.print(
        _simple_gradient(
            '♥ powered by argsense',
            (0x0A87EE, 0x9294F0) if color_seed == 'blue' else
            (0xF38CFD, 0xCE628C) if color_seed == 'magenta' else
            (0xF47FA4, 0xF49364) if color_seed == 'tan' else
            (0xFFFFFF, 0x909090) if color_seed == 'white' else
            _roll_color_pair()
        ),
        justify='right',
        style='bold',
        end=' \n',
    )


def _roll_color_pair() -> t.Tuple[int, int]:
    start = int('{:02x}{:02x}{:02x}'.format(
        randint(128, 255), randint(128, 255), randint(128, 255)
    ), 16)
    end = int('{:02x}{:02x}{:02x}'.format(
        randint(0, 127), randint(0, 127), randint(0, 127)
    ), 16)
    print(
        ':r',
        '[#{:06x}]#{:06x}[/] -> [#{:06x}]#{:06x}[/]'
        .format(start, start, end, end)
    )
    return start, end


def _simple_gradient(text: str, colors: t.Tuple[int, int]) -> rich.text.Text:
    color1, color2 = colors
    # print('{:06X}, {:06X}'.format(color1, color2), ':pv')
    text = rich.text.Text(text, style='bold')
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
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
