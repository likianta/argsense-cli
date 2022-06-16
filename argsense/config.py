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

FALLBACK_TYPE: t.Literal['any', 'str'] = 'any'  # see [./parser/func_parser.py]
FALLBACK_DESC = '[dim]no description[/]'
''' suggested:
        <empty string>
        [dim]no description[/]
        [dim]there is no description provided.[/]
    see also: [./cli.py : def show2() : def show()]
'''
FALLBACK_TO_HELP_IF_ARGPARSE_FAILED = False
#   see [./argparse/argv2.py : def report]

CMD_BORDER_STYLE = 'magenta'
ARG_BORDER_STYLE = 'blue'
OPT_BORDER_STYLE = 'grey74'
EXT_BORDER_STYLE = 'dim'
ERR_BORDER_STYLE = 'red'

ALIGN_ARGS_AND_OPTS_FIELD_WIDTH = False

WARNING_IF_RUNNING_ON_PYCHARM_CONSOLE = False
CONSOLE_WIDTH = None


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
