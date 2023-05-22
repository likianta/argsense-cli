"""
exposed colors:
    there are two types of color series you can use:
        1.  for standard color, for example 'red', 'blue', 'yellow', 'dim', etc.
            you can use the plain string directly.
        2.  for specific color for widgets and elements, for example the error
            panel, command panel, function description, etc. you should use the
            exposed [palette] object.
"""
from __future__ import annotations

import typing as t

__all__ = ['palette']


class T:
    _Color = str
    _ColorPair = t.Tuple[str, str]
    
    # noinspection PyTypedDict
    Palette = t.TypedDict('Palette', {
        'title': t.TypedDict('Title', {
            'python': _Color,
            '-m'    : _Color,
            '.py'   : _Color,
            '.exe'  : _Color,
        }),
        'panel': t.TypedDict('Panel', {
            'border': t.TypedDict('Border', {
                'group'    : _Color,
                'command'  : _Color,
                'argument' : _Color,
                'option'   : _Color,
                'extension': _Color,
                'error'    : _Color,
            }),
        }),
        'logo' : t.TypedDict('Logo', {
            'group'   : _ColorPair,
            'command' : _ColorPair,
            'argument': _ColorPair,
            'option'  : _ColorPair,
        }),
    })
    
    class Palette2:
        # noinspection PyPep8Naming
        class title:
            # noinspection PyPep8Naming
            class prog_name:
                python: str
                m: str
                py: str
                exe: str
            
            func_name: str
            arg1: str
            arg2: str
            kwarg1: str
            kwarg2: str
        
        # noinspection PyPep8Naming
        class panel:
            # noinspection PyPep8Naming
            class border:
                group: str
                command: str
                argument: str
                option: str
                extension: str
                error: str
            
            command_highlight: str
        
        # noinspection PyPep8Naming
        class logo:
            group: t.Tuple[str, str]
            command: t.Tuple[str, str]
            argument: t.Tuple[str, str]
            option: t.Tuple[str, str]


class BaseColor:
    blue = 'blue'
    cyan = 'cyan'
    default = 'default'
    dim = 'dim'
    magenta = 'magenta'
    red = 'red'
    yellow = 'yellow'


class Color(BaseColor):
    """
    inspired by [oh-my-posh/themes/bubbles <https://github.com/JanDeDobbeleer/
    oh-my-posh/blob/main/themes/bubbles.omp.json>]
    """
    blue = '#61afef'
    blue1 = '#61afef'
    blue2 = '#5f87ff'  # cornflower blue
    dark_magenta = '#8700af'
    deep_grey = '#bcbcbc'
    dim_acrylic = '#29315a'
    grey1 = '#777b7f'
    grey2 = '#909396'
    magenta = '#d08bf3'
    red = 'red'
    scarlet = '#e64747'
    tan = '#f49364'
    yellow = '#ffff00'
    yellow_accent = '#fffd3c'


class ColorPair:
    blue = ('#0a87ee', '#9294f0')  # calm blue -> light blue
    # blue = ('#2d34f1', '#9294f0')  # ocean blue -> light blue
    # magenta = ('#ed3b3b', '#d08bf3')  # rose red -> violet
    magenta = ('#f38cfd', '#d08bf3')  # light magenta -> violet
    tan = ('#f47fa4', '#f49364')  # cold sandy -> camel tan
    white = ('#ffffff', '#a8a8a8')  # bleach -> dim gray


color = Color()
color_pair = ColorPair()


class Palette:
    """
    ref: python use dot-notation to access dict elements:
        https://stackoverflow.com/a/54332748/9695911
    """
    
    def __init__(self, data: dict):
        # warning: make sure the key is a valid pattern as a attribute name.
        for k, v in data.items():
            if not isinstance(v, dict):
                setattr(self, k, v)
            else:
                setattr(self, k, Palette(v))


# noinspection PyTypeChecker
palette: T.Palette2 = Palette({
    'title': {
        'prog_name': {
            'python': color.default,
            'm'     : color.yellow,
            'py'    : color.scarlet,
            'exe'   : color.scarlet,
        },
        'func_name': color.magenta,
        'arg1'     : color.blue1,
        'arg2'     : color.blue2,
        'kwarg1'   : color.grey1,
        'kwarg2'   : color.grey2,
    },
    'panel': {
        'border'           : {
            'group'    : color.magenta,
            'command'  : color.tan,
            'argument' : color.blue,
            'option'   : color.deep_grey,
            'extension': color.dim,
            'error'    : color.red,
        },
        'command_highlight': f'{color.dark_magenta} on {color.yellow_accent}',
    },
    'logo' : {
        'group'   : color_pair.magenta,
        'command' : color_pair.tan,
        'argument': color_pair.blue,
        'option'  : color_pair.white,
    },
})
