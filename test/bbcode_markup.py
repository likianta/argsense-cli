from argsense import cli


@cli
def foo(color: str, date: str = '2024-01-01'):
    """
    [red]Hello[/] [blue]World![/]

    params:
        color: select one of the following colors:
            - [red]red[/]
            - [blue]blue[/]
            - [green]green[/]
            - [yellow]yellow[/]
        date: a date like [2024-01-01]. the bracketed text is safe here, -
            because the docstring markup parsing is disabled by default.
    """
    print(color, date)


@cli.cmd(rich=True)
def bar(color: str):
    """
    [red]Hello[/] [blue]World![/]

    params:
        color: select one of the following colors:
            - [red]red[/]
            - [blue]blue[/]
            - [green]green[/]
            - [yellow]yellow[/]
    """
    print(color)


if __name__ == '__main__':
    # by default, the docstring markup is NOT parsed (see `foo`):
    #   python test/bbcode_markup.py foo -h
    # enable it for a single command with `@cli.cmd(rich=True)` (see `bar`):
    #   python test/bbcode_markup.py bar -h
    cli.run()
