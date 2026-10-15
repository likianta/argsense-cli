from argsense import cli


def add(a: int, b: int):
    """
    Add two numbers.

    Params:
        a: The first number.
        b: The second number.
    """
    print(a + b)


def echo(text: str):
    """
    Print the given text back.

    Params:
        text: The text to echo.
    """
    print(text)


if __name__ == '__main__':
    # 1) scan this module and publish every public function as a command.
    #
    # python examples/02_multiple_functions.py -h
    # python examples/02_multiple_functions.py add 1 2
    # python examples/02_multiple_functions.py add --a 1 --b 2
    # python examples/02_multiple_functions.py echo -h
    # python examples/02_multiple_functions.py echo hi
    cli.run()

    # 2) pass a collection of functions instead of scanning the module.
    # cli.run((add, echo))

    # 3) the dict form additionally gives custom command names.
    # cli.run({'sum': add, 'echo': echo})
