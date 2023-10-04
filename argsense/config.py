"""
TODO:
    currently, the following options are defined but not used:
        ALIGN_ARGS_AND_OPTS_FIELD_WIDTH
        FALLBACK_TO_HELP_IF_ARGPARSE_FAILED
        FALLBACK_TYPE
        PRETTY_ERROR
        USE_RICH_MARKUP
"""
import typing as t


class T:
    ArgNameStyle = t.Literal['AAA_BBB', 'AAA-BBB', 'aaa_bbb', 'aaa-bbb', 'AaaBbb']
    FallbackType = t.Literal['any', 'str']
    OverwrittenScheme = t.Literal['first', 'last']
    TitleHeadStyle = t.Literal['system_dependent', 'fixed']


# appearance style
ALIGN_ARGS_AND_OPTS_FIELD_WIDTH = False
ARG_NAME_STYLE: T.ArgNameStyle = 'aaa-bbb'
PRETTY_ERROR = True
TITLE_HEAD_STYLE: T.TitleHeadStyle = 'system_dependent'
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

# fallback
BARE_NONE_MEANS_ANY = False
FALLBACK_TYPE: T.FallbackType = 'str'
#   see [./parser/func_parser.py : def parse_function()]
FALLBACK_DESC = '[dim]no description[/]'
''' suggested:
        <empty string>
        [dim]no description[/]
        [dim]there is no description provided.[/]
    see also: [./cli.py : def show2() : def show()]
'''
FALLBACK_TO_HELP_IF_ARGPARSE_FAILED = False
#   see [./argparse/argv.py : class ArgvVendor : def report()]
OVERWRITTEN_SCHEME: T.OverwrittenScheme = 'last'

# console related
WARNING_IF_RUNNING_ON_PYCHARM_CONSOLE = False
CONSOLE_WIDTH: int = 120

# other
WARN_IF_DUPLICATE_COMMANDS_OVERRIDDEN = False


# dynamic settings
class Dynamic:
    PREFERRED_FIELD_WIDTH_OF_NAME = 0
    PREFERRED_FIELD_WIDTH_OF_TYPE = 6  # the length of 'NUMBER'


def apply_changes():  # TODO: rename to 'finalize'?
    from .console import console
    if CONSOLE_WIDTH == 0:
        rulers = (80, 100, 120, 200)
        for x in reversed(rulers):
            if console.width > x:
                console.width = x
                break
    elif console.width > CONSOLE_WIDTH:
        console.width = CONSOLE_WIDTH
