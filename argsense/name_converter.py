from typing import Literal


def name_2_cname(name: str, is_option=False) -> str:
    # convert name from snake_case to kebab-case.
    name = name.lstrip('_').replace('_', '-')
    if is_option:
        name = '--' + name
    return name


def enrich_name(name: str, style: Literal[
    'cmd', 'arg', 'opt', 'ext',
]):
    """
    args:
        style: literal['cmd', 'arg', 'opt', 'ext']
    
    style:
        style   text color  name form
        -----   ----------  ------------------------------
        cmd     magenta     aaa-bbb
        arg     blue        aaa-bbb
        opt     default     --aaa-bbb/--not-aaa-bbb, -m/-M
        ext     dim         --aaa-bbb, -m
    """
    name = name.replace('_', '-')
    if style in ('opt', 'ext'): name = '--' + name
    
    if style == 'cmd':
        return f'[magenta]{name}[/]'
    elif style == 'arg':
        return f'[blue]{name}[/]'
    elif style == 'opt':
        return f'[default]{name}[/]'
    elif style == 'ext':
        return f'[dim]{name}[/]'
