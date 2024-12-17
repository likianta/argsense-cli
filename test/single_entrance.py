from argsense import cli


@cli.cmd()
def main(aaa: int, bbb: bool = True):
    print(aaa, bbb)


if __name__ == '__main__':
    # pox test/single_entrance.py -h
    cli.run(main)
