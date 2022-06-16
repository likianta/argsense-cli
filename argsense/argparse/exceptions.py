class ArgvParsingFailed(Exception):
    pass


class InsufficientParams(ArgvParsingFailed):
    def __str__(self):
        return 'Insufficient parameters.'


class MixinCase(ArgvParsingFailed):
    """ mix using upper and lower cases. for example '--xXxX'. """
    
    def __str__(self):
        return _dedent('''
            Mixed using upper and lower cases [dim](for example '--xXxX')[/].
            Be noted that argsense accepts only [yellow]total upper case[/] or -
            [cyan]total lower case[/].
            [dim]For [yellow]upper case[/] it is used only for [red]short[/], -
            [red]FLAG-typed[/], and [red]False-opinioned[/] options.[/]
        ''')


class ParamAheadOfCommand(ArgvParsingFailed):
    def __str__(self):
        # return 'You cannot put parameters ahead of command!'
        return _dedent('''
            You cannot put parameters ahead of command!
            For example:
                [red]Wrong:[/]
                    python3 main.py [red]--username XXX[/] login
                [green]Correct:[/]
                    python3 main.py login [green]--username XXX[/]
        ''')


class ParamNotFound(ArgvParsingFailed):
    
    def __init__(self, command: str, param: str):
        self.command = command
        self.param = param
    
    def __str__(self):
        return _dedent('''
            The param [red]"{param}"[/] is not found in command -
            ([cyan]{command}[/]) parameters. It maybe a typo or surplus problem.
            Please check your command `--help` and try again.
        ''').format(param=self.param, command=self.command)


class ShortOptionFormat(ArgvParsingFailed):
    
    def __init__(self, param: str):
        self.param = param
    
    def __str__(self):
        return _dedent('''
            The short option name form is not correct.
            It should be [cyan]"-xxx"[/] or [cyan]"-XXX"[/], but given -
            [red]"{param}"[/].
        ''').format(param=self.param)


class TooManyArguments(ArgvParsingFailed):
    def __str__(self):
        return 'Too many arguments!'


class TypeConversionError(ArgvParsingFailed):
    
    def __init__(self, expected_type: str, given_type: str):
        self.expected_type = expected_type
        self.given_type = given_type
    
    def __str__(self):
        return _dedent('''
            The given type [red]{given_type}[/] is not compatible with -
            expected type: [cyan]{expected_type}[/].
        ''').format(
            expected_type=self.expected_type,
            given_type=self.given_type
        )


class TypeNotCorrect(ArgvParsingFailed):
    
    def __init__(self, expected_type: str):
        self.expected_type = expected_type
    
    def __str__(self):
        return f'Expect type [cyan]{self.expected_type}[/].'


def _dedent(text: str) -> str:
    import re
    from textwrap import dedent
    # return dedent(text).strip().replace(' -\n', ' ')
    return re.sub(r' - *\n', ' ', dedent(text).strip())
