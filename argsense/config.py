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

from rich import get_console


class T:
    ArgNameStyle = t.Literal[
        'AAA_BBB', 'AAA-BBB', 'aaa_bbb', 'aaa-bbb', 'AaaBbb'
    ]
    FallbackType = t.Literal['any', 'str']
    OverwrittenScheme = t.Literal['first', 'last']


# -----------------------------------------------------------------------------
# v1.0.0+

ALLOW_HSHORT_TO_BE_REDEFINED = True
#   related: /test/hshort_is_occupied_by_normal_param.py
HIDE_UNSTATED_VARIABLE_KWARGS = True
'''
    for example:
        def foo(aaa, **kwargs):
            """
            params:
                **kwargs:
                    bbb: ...
                    ccc: ...
            """
    if `HIDE_UNSTATED_VARIABLE_KWARGS` is true, "bbb" and "ccc" will be -
    displayed.
    if false, in addition to "bbb" and "ccc", there will be an ellipsis -
    ("...") shown in the last place.
    see also: "./renderer/rich/render.py : [def] render_function_parameters : -
    [code] 'if func_info.args4: ...'"
'''
POST_LOGO_IN_HELP_INTERFACE = True
PROGRAM_NAME_STYLE = 'fixed'
'''
    type: 'fixed' | 'system_dependent'
    illustration:
        system      style='fixed'   style='system_dependent'
        -------     -------------   ------------------------
        unix        python          python3
        unix        python -m       python3 -m
        windows     python          py
        windows     python -m       py -m
        windows     xxx.exe         xxx.exe
    see also: `./renderer/rich/render2.py : [def] _detect_program_name`
'''

# -----------------------------------------------------------------------------
# TODO: need refactoring

# DELETE: appearance style
ALIGN_ARGS_AND_OPTS_FIELD_WIDTH = False
ARG_NAME_STYLE: T.ArgNameStyle = 'aaa-bbb'
PRETTY_ERROR = True
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
    console = get_console()
    if CONSOLE_WIDTH == 0:
        rulers = (80, 100, 120, 200)
        for x in reversed(rulers):
            if console.width > x:
                console.width = x
                break
    elif console.width > CONSOLE_WIDTH:
        console.width = CONSOLE_WIDTH
