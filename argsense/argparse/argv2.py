from __future__ import annotations

import typing as t


class ArgvVendor:
    
    def __init__(self, argv: list[str]):
        self.argv = argv
        self.pointer = 0
    
    def __iter__(self) -> t.Iterator[str]:
        for i, arg in enumerate(self.argv):
            self.pointer = i
            if i == 0:
                continue
            yield arg
    
    def report(self, msg: str):
        from rich.panel import Panel
        from textwrap import dedent
        from ..console import console
        
        console.print(Panel(dedent('''
            Failed parsing command line arguments -- there was an error -
            happened in the following position:
            
            {argv}
            {indicator}
            
            {reason}
        ''').strip().replace(' -\n', ' ').format(
            argv=' '.join(self.argv),
            #   TODO: highlight the command line.
            indicator='{spaces}[red]{wave}[/]'.format(
                spaces=' ' * len(' '.join(self.argv[:self.pointer])),
                wave='~' * len(self.argv[self.pointer])
            ),
            reason=msg
        ), title='Argparsing failed', title_align='left'))
