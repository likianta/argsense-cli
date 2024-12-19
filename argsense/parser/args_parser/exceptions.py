import re
import textwrap
import typing as t


class ArgvParsingFailed(Exception):
    def __init__(self, index: int):
        self.index = index


class InsufficientArguments(ArgvParsingFailed):
    def __init__(self, index: int, args: t.Tuple[str, ...] = None) -> None:
        self.index = index
        self.args = args
    
    def __str__(self) -> str:
        if self.args is None:
            return 'Insufficient arguments!'
        else:
            return _dedent(
                '''
                Insufficient arguments! You may miss the following arguments:
                {args}
                '''
            ).format(
                args=textwrap.indent(
                    '\n'.join(f'[dim]-[/] {x.upper()}' for x in self.args),
                    '    '
                )
            )


class MixinCase(ArgvParsingFailed):
    """ mix using upper and lower cases. for example '--xXxX'. """
    
    def __str__(self) -> str:
        return _dedent(
            '''
            Mixed using upper and lower cases [dim](for example '--xXxX')[/].
            Be noted that argsense accepts only [yellow]total upper case[/] or -
            [cyan]total lower case[/].
            [dim]For [yellow]upper case[/] it is used only for [red]short[/], -
            [red]FLAG-typed[/], and [red]False-opinioned[/] options.[/]
            '''
        )


class ParamAheadOfCommand(ArgvParsingFailed):
    def __str__(self) -> str:
        # return 'You cannot put parameters ahead of command!'
        return _dedent(
            '''
            You cannot put parameters ahead of command!
            For example:
                [red]Wrong:[/]
                    python3 main.py [red]--username XXX[/] login
                [green]Correct:[/]
                    python3 main.py login [green]--username XXX[/]
            '''
        )


class ParamNotFound(ArgvParsingFailed):
    def __init__(
        self, index: int, param: str, candidates: t.Iterable[str]
    ) -> None:
        self.index = index
        self.param = param
        self.candidates = candidates
    
    def __str__(self) -> str:
        if x := did_you_mean(self.param, self.candidates):
            return _dedent(
                '''
                Parameter "{}" not found, did you mean "{}"?
                '''
            ).format(self.param, x)
        else:
            return _dedent(
                '''
                Parameter "{}" not found, it may be a typo or redundant name.
                Please check your command `--help` for more information.
                '''
            ).format(self.param)


class ShortOptionFormat(ArgvParsingFailed):
    def __init__(self, index: int, param: str) -> None:
        self.index = index
        self.param = param
    
    def __str__(self) -> str:
        return _dedent(
            '''
            The short option name form is not correct.
            It should be [cyan]"-xxx"[/] or [cyan]"-XXX"[/], but given -
            [red]"{param}"[/].
            '''
        ).format(param=self.param)


class TooManyArguments(ArgvParsingFailed):
    def __str__(self) -> str:
        return 'Too many arguments!'


class TypeConversionError(ArgvParsingFailed):
    def __init__(self, index: int, expected_type: str, given_type: str) -> None:
        self.index = index
        self.expected_type = expected_type
        self.given_type = given_type
    
    def __str__(self) -> str:
        return _dedent(
            '''
            The given type [red]{given_type}[/] is not compatible with -
            expected type [cyan]{expected_type}[/].
            '''
        ).format(
            expected_type=self.expected_type,
            given_type=self.given_type
        )


class TypeNotCorrect(ArgvParsingFailed):
    def __init__(self, index: int, expected_type: str) -> None:
        self.index = index
        self.expected_type = expected_type
    
    def __str__(self) -> str:
        return f'Expect type [cyan]{self.expected_type}[/].'


def did_you_mean(
    wrong_word: str, known_words: t.Iterable[str]
) -> t.Optional[str]:
    """ a simple function to find the closest word.

    this function is served for the following cases:
        - user types a wrong command name
        - user types a wrong option name
    see also:
        - [./cli.py : def run() : KeyError occurance]
        - [./argparse/parser.py : def parse_sys_argv()]

    note: we are using the built-in library - [#1 difflib] - to implement this.

    [#1: https://docs.python.org/3/library/difflib.html]
    """
    from difflib import get_close_matches
    if r := get_close_matches(wrong_word, known_words, n=1, cutoff=0.7):
        return str(r[0])
    else:
        return None


def _dedent(text: str) -> str:
    return re.sub(r' - *\n', ' ', textwrap.dedent(text).strip())
