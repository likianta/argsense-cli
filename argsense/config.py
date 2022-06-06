import typing as _t

USE_RICH_MARKUP = True
DEFAULT_TEXT_FOR_NO_DESC = ''
#   suggested alternative: '[dim]no description[/]'

CONSOLE_WIDTH = None
FALLBACK_TYPE = 'any'  # type: _t.Literal['any', 'str']

CMD_BORDER_STYLE = 'magenta'
ARG_BORDER_STYLE = 'blue'
OPT_BORDER_STYLE = 'grey74'
EXT_BORDER_STYLE = 'dim'

ERR_BORDER_STYLE = 'red'


def apply_changes():
    if CONSOLE_WIDTH is not None:
        from .console import console
        console.width = CONSOLE_WIDTH
    if FALLBACK_TYPE == 'str':
        # TODO: see [./parser/func_parser.py : def parse_function].
        pass
