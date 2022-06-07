import typing as _t

USE_RICH_MARKUP = True

FALLBACK_TYPE = 'any'  # type: _t.Literal['any', 'str']
FALLBACK_DESC = ''
# suggested:
#   <empty string>
#   [dim]no description[/]
#   [dim]there is no description provided.[/]

CMD_BORDER_STYLE = 'magenta'
ARG_BORDER_STYLE = 'blue'
OPT_BORDER_STYLE = 'grey74'
EXT_BORDER_STYLE = 'dim'
ERR_BORDER_STYLE = 'red'

CONSOLE_WIDTH = None

EXPAND_HELP_INFO = 0  # int[0, 1, 2]
#   0: the default help method.
#   1: add title line for each command item.
#   2: iterate all commands help method after showing commands panel.


class Dynamic:
    PREFERRED_FIELD_WIDTH_OF_NAME = 0
    PREFERRED_FIELD_WIDTH_OF_TYPE = len('NUMBER')


def apply_changes():
    if CONSOLE_WIDTH is not None:
        from .console import console
        console.width = CONSOLE_WIDTH
    if FALLBACK_TYPE == 'str':
        # TODO: see [./parser/func_parser.py : def parse_function].
        pass
