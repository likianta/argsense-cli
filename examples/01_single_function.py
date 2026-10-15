from argsense import cli


def hello(name: str):
    """
    Greet someone.

    Params:
        name: Who to greet.
    """
    print(f'Hello {name}!')


if __name__ == '__main__':
    # a single function as the only entrance.
    #
    # python examples/01_single_function.py
    # python examples/01_single_function.py -h
    # python examples/01_single_function.py Alice
    # python examples/01_single_function.py --name Alice
    cli.run(hello)
