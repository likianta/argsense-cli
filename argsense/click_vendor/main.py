import os
import re
import typing as t


def expand_args(
        args: t.Iterable[str],
        *,
        user: bool = True,
        env: bool = True,
        glob_recursive: bool = True,
) -> t.List[str]:
    """Simulate Unix shell expansion with Python functions.

    See :func:`glob.glob`, :func:`os.path.expanduser`, and
    :func:`os.path.expandvars`.

    This is intended for use on Windows, where the shell does not do any
    expansion. It may not exactly match what a Unix shell would do.

    :param args: List of command line arguments to expand.
    :param user: Expand user home directory.
    :param env: Expand environment variables.
    :param glob_recursive: ``**`` matches directories recursively.

    .. versionchanged:: 8.1
        Invalid glob patterns are treated as empty expansions rather
        than raising an error.

    .. versionadded:: 8.0

    :meta private:
    """
    from glob import glob
    
    out = []
    
    for arg in args:
        if user:
            arg = os.path.expanduser(arg)
        
        if env:
            arg = os.path.expandvars(arg)
        
        try:
            matches = glob(arg, recursive=glob_recursive)
        except re.error:
            matches = []
        
        if not matches:
            out.append(arg)
        else:
            out.extend(matches)
    
    return out
