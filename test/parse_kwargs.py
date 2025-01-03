from argsense import cli


@cli.cmd()
def main(aaa, bbb=None, **ccc):
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    # pox test/parse_kwargs.py -h
    # pox test/parse_kwargs.py mmm nnn --ooo ppp
    cli.run(main)
