import typing as t

# -----------------------------------------------------------------------------
# rich style

TITLE_HEAD_STYLE: t.Literal['system_dependent', 'fixed'] = 'system_dependent'
''' the difference:
        system      system_dependent    fixed
        ------      ----------------    -----
        unix        python3             python
        unix        python3 -m          python -m
        windows     py                  python
        windows     py -m               python -m
        windows     xxx.exe             xxx.exe
'''
USE_RICH_MARKUP = True

# TODO: not used yet. see also `./parser/func_parser.py`
FALLBACK_TYPE: t.Literal['any', 'str'] = 'any'
FALLBACK_DESC = ''
''' suggested:
        <empty string>
        [dim]no description[/]
        [dim]there is no description provided.[/]
'''

CMD_BORDER_STYLE = 'magenta'
ARG_BORDER_STYLE = 'blue'
OPT_BORDER_STYLE = 'grey74'
EXT_BORDER_STYLE = 'dim'
ERR_BORDER_STYLE = 'red'

ALIGN_ARGS_AND_OPTS_FIELD_WIDTH = False

WARNING_IF_RUNNING_ON_PYCHARM_CONSOLE = False
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
        if console.width > CONSOLE_WIDTH:
            console.width = CONSOLE_WIDTH
    if FALLBACK_TYPE == 'str':
        # TODO: see [./parser/func_parser.py : def parse_function].
        pass
