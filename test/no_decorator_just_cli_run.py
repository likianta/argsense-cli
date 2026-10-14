from argsense import cli


def foo():
    ...


def bar():
    ...


def baz():
    ...


if __name__ == '__main__':
    # 1) scan the calling module and expose every public function.
    #    this is the decorator-free form, and the most concise one.
    cli.run()

    # 2) use a single function as the only entrance.
    # cli.run(foo)

    # 3) pass a group of functions.
    # cli.run((foo, bar))

    # 4) pass a dict to give custom command names.
    # cli.run({
    #     'foo': foo,
    #     'baring': bar,
    # })
