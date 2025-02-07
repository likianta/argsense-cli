import os
import sys
import typing as t
from textwrap import dedent

import rich
import rich.panel

# print(sys.argv, ':v')

_DEBUG = os.getenv('ARGSENSE_DEBUG') == '1'


class T:
    ArgvArgs = t.Tuple[str, ...]
    ArgvTarget = t.Tuple[str]
    ArgvLauncher = t.Tuple[str, ...]


class Argv:
    launcher: T.ArgvLauncher
    target: T.ArgvTarget
    args: T.ArgvArgs
    
    @property
    def possible_function(self) -> t.Optional[str]:  # FIXME: not reliable
        for x in self.args:
            if not x.startswith(('_', '-')):
                return x.replace('_', '-')
    
    @classmethod
    def from_sys_argv(cls, argv: t.Sequence[str]) -> 'Argv':
        """
        note: this method should be called after main modules loaded. i.e. you -
        can not call this in global scope.
        
        params:
            argv: by default use `sys.orig_argv`
                it looks like:
                    ['python', 'test.py', 'foo', '--bar', 'baz']
                    ['python', '-m', 'test', 'foo', '--bar', 'baz']
        
        returns:
            e.g.
                Argv(
                    launcher=('python',),
                    target=('test.py',),
                    args=('foo', '--bar', 'baz'),
                    argx=2
                )
                Argv(
                    launcher=('python', '-m'),
                    target=('test',),
                    args=('foo', '--bar', 'baz'),
                    argx=3
                )
        """
        # print(argv, ':pv')
        if argv[1] == '-m':
            return Argv((sys.executable, '-m'), (argv[2],), tuple(argv[3:]))
        else:
            return Argv((sys.executable,), (argv[1],), tuple(argv[2:]))
    
    def __init__(
        self,
        launcher: T.ArgvLauncher,
        target: T.ArgvTarget,
        args: T.ArgvArgs
    ) -> None:
        self.launcher = launcher
        self.target = target
        self.args = args
        self.argx = len(launcher) + len(target)
    
    def __iter__(self) -> t.Iterator[t.Tuple[int, str, int]]:
        """
        yields:
            ((index, arg, type_code), ...)
        """
        i = -1
        for x in self.launcher + self.target:
            i += 1
            yield i, x, 0
        for x in self.args:
            i += 1
            yield i, x, 1


def report(err_idx: int, err_msg: str, err_type: str = None) -> None:
    """
    accurately report which element is parsing failed.
    
    conception:
        input: py test.py foo --bar baz
        report:
            > python test.py foo --bar baz
            `--bar` was not recognized as a valid option in `foo` command. did
            you mean "--bart"?
    
    see also:
        ./exceptions.py
    """
    xlist = ['python'] + sys.argv
    if 0 <= err_idx < len(xlist):
        xlist[err_idx] = '[red u]{}[/]'.format(xlist[err_idx])
    else:
        xlist.append('[red dim u]???[/]')
    
    rich.print(
        rich.panel.Panel(
            dedent(
                '''
                Failed parsing command line arguments -- there was an error \\
                happened in the following position:

                [default on #1d1d1d] [bold cyan]>[/] {argv} [/]

                {reason}
                '''
            ).strip().replace(' \\\n', ' ').format(
                argv=' '.join(xlist),
                reason=err_msg,
            ),
            border_style='red',
            title='\\[argsense{}] argparsing failed'.format(
                f'.{err_type}' if err_type else ''
            ),
            title_align='left',
        )
    )
    
    exit(1)
