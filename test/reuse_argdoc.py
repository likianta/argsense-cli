from argsense import cli


@cli
def foo(name: str):
    """
    params:
        name: Leader personal stage system impact fear itself short.
    """


@cli
def bar(name: str):
    """
    params:
        name: see `@foo:name`
    """


if __name__ == '__main__':
    # python test/reuse_argdoc.py foo -h
    # python test/reuse_argdoc.py bar -h
    cli.run()
