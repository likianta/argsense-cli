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
        self.pointer = 0
    
    def report(self, msg: str):
        """
        accurately report that which element is parsing failed.
        
        conception:
            input: py test.py foo --bar baz
            report:
                py test.py foo --bar baz
                               ~~~~~
                    `--bar` was not recognized as a valid option in `foo`
                    command. did you mean "--bart"?
        
        see also:
            ./exceptions.py
        """
        from rich.panel import Panel
        from textwrap import dedent
        from ..console import console
        
        def create_argv_string():
            # TODO: highlight the command line.
            # scheme A
            if self.pointer == 0:
                return ' '.join(self.argv) + ' [dim]???[/]'
            else:
                return '{} [red]{}[/] {}'.format(
                    ' '.join(self.argv[:self.pointer]),
                    self.argv[self.pointer],
                    ' '.join(self.argv[self.pointer + 1:]),
                )
            # scheme B (abandoned)
            # # out = ' '.join(self.argv)
            # # if self.pointer == 0:
            # #     return out + ' [dim]???[/]'
            # # else:
            # #     return out
        
        def create_indicator():
            if self.pointer:
                return '{spaces} [red dim]{wave}[/]'.format(
                    spaces=' ' * len(' '.join(self.argv[:self.pointer])),
                    wave='~' * len(self.argv[self.pointer])
                )
            else:
                return '{spaces} [red dim]~~~[/]'.format(
                    spaces=' ' * len(' '.join(self.argv))
                )
        
        console.print(Panel(
            dedent('''
                Failed parsing command line arguments -- there was an error -
                happened in the following position:
                
                [bold cyan]>[/] {argv}
                  {indicator}
                {reason}
            ''').strip().replace(' -\n', ' ').format(
                argv=create_argv_string(),
                indicator=create_indicator(),
                reason=msg
            ),
            border_style='red',
            title='\\[argsense] argparsing failed',
            title_align='left',
        ))
        
        # from ..config import FALLBACK_TO_HELP_IF_ARGPARSE_FAILED
        # if FALLBACK_TO_HELP_IF_ARGPARSE_FAILED:
        #     pass
        
        exit(1)


def _did_you_mean(wrong_word: str, known_words: t.Iterable[str]) -> str | None:
    """ a simple function (no third party dependency) to find the closest word.
    
    note: we are using the built-in library - [#1 difflib] - to implement this.
    
    [#1: https://docs.python.org/3/library/difflib.html]
    
    TODO: this function is created but not used yet. i will use it in further
        version. see also [./exceptions.py : class ParamNotFound].
    """
    from difflib import get_close_matches
    if r := get_close_matches(wrong_word, known_words, n=1, cutoff=0.8):
        return str(r[0])
    else:
        return None
