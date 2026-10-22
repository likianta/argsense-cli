"""
Reading form values off a command line.

Both forms open with what the line already said: `python main.py Alice 22`
draws a tui / gui whose boxes hold those values. The parsing is shared here;
how a value is then spelled in a widget is up to the renderer (the tui works
in text, the gui in typed values).
"""

import typing as tp

from ..parser import Argv
from ..parser import FuncInfo
from ..parser import parse_argv
from ..parser.args_parser import exceptions as e

InitialValues = tp.Dict[str, tp.Any]
#   form values of one command, keyed by the python param name
InitialsMap = tp.Dict[str, InitialValues]
#   form values of every command, keyed by the command name


def front_matter(func_info: FuncInfo) -> dict:
    """
    The same `front_matter` that the cli interface hands to the parser.
    """
    return {
        'args': {k: v['ctype'] for k, v in func_info.args.items()},
        'kwargs': {k: v['ctype'] for k, v in func_info.extended_kwargs.items()},
        'index': func_info.cname_2_name,
    }


def collect_initial_values(func_info: FuncInfo, argv: Argv) -> InitialValues:
    """
    Best effort: map a command line onto form values, keeping the types.

    Only the parameters the user actually gave are returned, and a command
    line that does not parse at all simply yields nothing.
    """
    try:
        result = parse_argv(
            argv,
            mode='command',
            front_matter=front_matter(func_info),  # type: ignore
            implicit_help=False,
            raise_on_error=True,
        )
    except e.ArgvParsingFailed:
        return {}

    assert result is not None
    infos = {**func_info.args, **func_info.kwargs}
    values: InitialValues = {}
    for name, value in {**result['args'], **result['kwargs']}.items():
        info = infos.get(name)
        if info is None:
            continue
        if value == info.get('default', ...):
            # not given by the user; the form shows the default anyway.
            continue
        values[name] = value
    return values


def resolve_initials(
    func_infos: tp.Sequence[FuncInfo], argv: tp.Optional[Argv]
) -> tp.Tuple[InitialsMap, str]:
    """
    Work out the form values of every command from a command line, and tell
    which command the command line refers to (its tab is opened first).

    Returns `(initials, active_command_name)`.
    """
    func_infos = list(func_infos)
    initials: InitialsMap = {fi.name: {} for fi in func_infos}
    active = func_infos[0].name
    if argv is None:
        return initials, active

    if len(func_infos) == 1:
        initials[func_infos[0].name] = collect_initial_values(
            func_infos[0], argv
        )
        return initials, active

    # multi-command: the first positional token is the command name, and the
    # tokens that follow it are that command's arguments.
    tokens = list(argv.args)
    for i, token in enumerate(tokens):
        if token.startswith(('-', '_')):
            continue
        target = next((x for x in func_infos if x.name == token), None)
        if target is not None:
            active = target.name
            sub_argv = Argv(argv.launcher, argv.target, tuple(tokens[i + 1 :]))
            initials[target.name] = collect_initial_values(target, sub_argv)
        break
    return initials, active
