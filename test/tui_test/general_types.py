from argsense import tui
from neoprint import print


def main(name: str, age: int):
    """general types demo.

    params:
        name: your name.
        age: your age.
    """
    print(name, age)


if __name__ == '__main__':
    # TODO:
    #   tui has the same API as `argsense.cli`
    #   tui.run(..., inline=True): see textual inline feature
    tui.run(main, inline=True)
    # tui.run(main, inline=False)
