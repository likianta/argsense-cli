from argsense import cli


@cli.cmd()
def main(x: str) -> None:
    if x == '':
        print('`x` is an empty string', ':v4')
    else:
        print('incorrct value for `x`: {}'.format(x), ':v8')


if __name__ == '__main__':
    # pox test/pass_empty_argument.py ''
    # pox test/pass_empty_argument.py :empty
    cli.run(main)
