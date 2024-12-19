from argsense import cli


@cli.cmd()
def main(x: str) -> None:
    print(x, x == '')


if __name__ == '__main__':
    # pox test/pass_empty_argument.py ''
    # pox test/pass_empty_argument.py :empty
    cli.run(main)
