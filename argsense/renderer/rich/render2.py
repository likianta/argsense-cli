import math
import os
import sys
import typing as t

import rich.box
import rich.padding
import rich.panel
import rich.table
import rich.text

from . import artist
from .style import color
from ... import config
from ...cli import CommandLineInterface
from ...console import console
from ...parser import FuncInfo


def render(
    self: CommandLineInterface,
    func: t.Optional[t.Callable],
    **_
) -> None:
    func_info: FuncInfo
    
    if func is None:
        raise NotImplementedError
    else:
        func_info = self.commands[id(func)]
        has_params = bool(func_info.args or func_info.func_kwargs)
    
    if not has_params:
        raise NotImplementedError

    console.print(
        _simple_gradient(
            '{} {} {}'
            .format(
                _detect_program_name(),
                func_info.name,
                '...' if has_params else ''
            )
            .strip(),
            0xFF0000,  # red
            0xFFFF00,  # yellow
            # int('{:02X}{:02X}{:02X}'.format(
            #     randint(0x80, 0xFF), randint(0x80, 0xFF), randint(0x80, 0xFF)
            # ), 16),
            # int('{:02X}{:02X}{:02X}'.format(
            #     randint(0x00, 0x80), randint(0x00, 0x80), randint(0x00, 0x80)
            # ), 16),
        ),
        justify='center'
    )
    
    if func_info.desc:
        console.print(
            rich.padding.Padding(
                rich.text.Text(func_info.desc, style='gray70'),
                (0, 2, 0, 2)
            )
        )
    
    if has_params:
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
        table.add_column('index', style=color.yellow + ' dim')
        table.add_column('param', style=color.blue + ' bold')
        table.add_column('short', style=color.green + ' bold')
        table.add_column('type', style='dim')
        table.add_column('description', style=None, ratio=1)
        table.add_column('default', style=color.scarlet)
        
        i = 0
        for arg in func_info.args.values():
            i += 1
            name, short = (
                arg['cname'].split(', ') if ', ' in arg['cname']
                else (arg['cname'], '')
            )
            table.add_row(
                '*',
                str(i) + '   ',
                name + '   ',
                short + '   ',
                arg['ctype'].name + '   ',
                arg['desc'],
            )
        for arg in func_info.func_kwargs.values():
            i += 1
            name, short = (
                arg['cname'].split(', ') if ', ' in arg['cname']
                else (arg['cname'], '')
            )
            table.add_row(
                ' ',
                str(i) + '   ',
                name.lstrip('-') + '   ',  # FIXME: is this good?
                short + '   ',
                arg['ctype'].name + '   ',
                arg['desc'],
                '   ' + 'default={}'.format(
                    arg['default'] if arg['default'] != '' else '""'
                ),
            )
        console.print(
            rich.panel.Panel(
                table,
                border_style=color.blue,
                padding=(0, 2),
                title='Parameters',
                title_align='right',
            )
        )
    
    console.print(
        artist.post_logo(style='option'),
        justify='right',
        style='bold',
        end=' \n'
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
        return _simple_gradient(text, *colors)
    else:
        text_parts = []
        substr_len = math.ceil(len(text) / len(colors))
        for i in range(len(colors) - 1):
            text_parts.append(
                _simple_gradient(
                    text[(i * substr_len):((i + 1) * substr_len)],
                    colors[i],
                    colors[i + 1]
                )
            )
        return rich.text.Text.assemble(*text_parts)


def _simple_gradient(text, color1: int, color2: int) -> rich.text.Text:
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
