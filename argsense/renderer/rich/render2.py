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

from .style import color
from ... import config
from ...cli import CommandLineInterface
from ...console import console
from ...converter import val_2_cval
from ...parser import FuncInfo


def render(
    self: CommandLineInterface,
    func: t.Optional[t.Callable],
    *,
    show_func_name_in_title: bool = True,
) -> None:
    func_info: FuncInfo
    
    if func is None:
        raise NotImplementedError
    else:
        func_info = self.commands[id(func)]
        has_args = bool(func_info.args or func_info.kwargs)
        has_var_args = '*' in func_info.args
        has_var_kwargs = '**' in func_info.kwargs
    
    if not has_args:
        raise NotImplementedError
    
    title_parts = [_detect_program_name()]
    if show_func_name_in_title:
        title_parts.append(func_info.name)
    if has_args:
        title_parts.append('...')
    console.print(
        _simple_gradient(
            ' '.join(title_parts),
            (0xFF0000, 0xFFFF00)  # red -> yellow
        ),
        justify='center',
        style='bold',
    )
    
    if func_info.desc:
        console.print(
            rich.padding.Padding(
                rich.text.Text(func_info.desc, style='gray70'),
                (0, 2, 0, 2)
            )
        )
    
    if has_args:
        table = rich.table.Table.grid(expand=True, padding=(0, 1))
        #   padding=(0, 1): vertical padding 0, horizontal padding 1.
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
            table.add_row(
                '*',
                '{:<4}'.format(i),
                name + '   ',
                short + '   ',
                arg['ctype'].name + '   ',
                arg['desc'],
            )
        if has_var_args:
            table.add_row(
                ' ',
                '*',
                func_info.args['*']['cname'],
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
            table.add_row(
                ' ',
                '-   ' if has_var_args else '{:<4}'.format(i),
                name.lstrip('-') + '   ',  # FIXME: is this good?
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
    
    # logo
    console.print(
        _simple_gradient(
            '♥ powered by argsense',
            (0xFFFFFF, 0xA8A8A8)
            # _roll_color_pair()
        ),
        justify='right',
        style='bold',
        end=' \n',
    )


def _detect_program_name() -> str:
    """
    code reference: `lib click : /utils.py : def _detect_program_name()`
    
    returns e.g.:
        - 'python example.py'
        - 'python -m example'
        - 'python3 example.py'
        - 'python3 -m example'
        - 'example.exe'
    """
    # print(sys.orig_argv, ':v')
    
    main = sys.modules['__main__']
    path = sys.orig_argv[1]
    name = os.path.splitext(os.path.basename(path))[0]
    
    head = 'python' if config.TITLE_HEAD_STYLE == 'fixed' else (
        'python' if os.name == 'nt' else 'python3'
    )
    
    if getattr(main, '__package__', None) is None:
        return f'{head} {name}.py'
    elif (
        os.name == 'nt'
        and main.__package__ == ''
        and not os.path.exists(path)
        and os.path.exists(f'{path}.exe')
    ):
        return f'{name}.exe'
    
    py_module = t.cast(str, main.__package__)
    if name != '__main__':  # a submodule like 'example.cli'
        py_module = f'{py_module}.{name}'.lstrip('.')
    
    return f'{head} -m {py_module}'


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
    
    
def _roll_color_pair() -> t.Tuple[int, int]:
    return (
        int('{:02x}{:02x}{:02x}'.format(
            randint(128, 255), randint(128, 255), randint(128, 255)
        ), 16),
        int('{:02x}{:02x}{:02x}'.format(
            randint(0, 127), randint(0, 127), randint(0, 127)
        ), 16),
    )


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
