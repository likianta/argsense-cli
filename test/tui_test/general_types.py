from argsense import tui
from neoprint import print


def main(name: str, age: int):
    print(name, age)


if __name__ == '__main__':
    # TODO:
    #   tui has the same API as `argsense.cli`
    #   tui.run(..., inline=True): see textual inline feature
    #       1. show inline tui
    #       2. user clicks run button, it goes into regular console output
    tui.run(main, inline=True)
