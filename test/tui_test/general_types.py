from argsense import cli
# from neoprint import print


def main(name: str, age: int):
    """
    General types demo.

    Params:
        name: Your name.
        age: Your age.
    """
    print(name, age)


if __name__ == '__main__':
    cli.run(main, mode='tui')
