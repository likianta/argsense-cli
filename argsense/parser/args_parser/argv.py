import sys
import typing as t
from textwrap import dedent

import rich
import rich.panel


class OrigSysArgvInfo:
    """ wrapper for `sys.org_argv`. """
    argv: t.Tuple[str, ...]
    command: str
    exec_path: str
    main_args: t.Tuple[str, ...]
    target: str
    _is_package_mode: bool
    
    def __init__(self) -> None:
        # note: python 3.8 has no `sys.orig_argv`
        if hasattr(sys, 'orig_argv'):
            self.argv = tuple(sys.orig_argv)  # TODO
        else:
            # print(
            #     ':vl',
            #     sys.modules['__main__'],
            #     {
            #         k: getattr(sys.modules['__main__'], k)
            #         for k in dir(sys.modules['__main__'])
            #     },
            # )
            if sys.argv[0] == '-m':
                self.argv = (
                    sys.executable,
                    '-m',
                    sys.modules['__main__'].__package__ or 'argsense',
                    *sys.argv[1:]
                )
            else:
                self.argv = (sys.executable, *sys.argv)
        # print(':lv', {
        #     'sys.orig_argv': getattr(sys, 'orig_argv', (
        #         'NO_ORIG_ARGV', sys.version.split()[0]
        #     )),
        #     'sys.argv'     : sys.argv,
        #     'self.argv'    : self.argv,
        # })
        self._is_package_mode = self.argv[1] == '-m'
        self.main_args = (
            self.argv[3:] if self._is_package_mode else self.argv[2:]
        )
        self.exec_path = self.argv[0]
        self.target = self.argv[2] if self._is_package_mode else self.argv[1]
        self.command = ''
        for x in self.main_args:
            if not x.startswith('-'):
                self.command = x.replace('_', '-')  # FIXME: not reliable
                break
    
    def __iter__(self) -> t.Iterator[t.Tuple[int, str, int]]:
        """
        yields:
            ((index, arg, type_code), ...)
        """
        for i, arg in enumerate(self.argv):
            t = 1
            if self._is_package_mode:
                if i in (0, 1, 2):
                    t = 0
            else:
                if i in (0, 1):
                    t = 0
            yield i, arg, t


argv_info = OrigSysArgvInfo()


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
    xlist = list(argv_info.argv)
    xlist[0] = 'python'
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
