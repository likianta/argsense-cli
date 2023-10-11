from argsense import cli


@cli.cmd()
def main(aaa: int, bbb: int = 1) -> None:
    print(f'{aaa = }, {bbb = }')


if __name__ == '__main__':
    # pox unittests/pass_kw_to_args.py -h
    # pox unittests/pass_kw_to_args.py --aaa 0 --bbb 1
    cli.run(main)
