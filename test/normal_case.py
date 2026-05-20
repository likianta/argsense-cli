from argsense import cli
from neoprint import print


@cli
def foo(aaa: str, bbb: str = '', ccc: bool = True) -> None:
    print(aaa, bbb, ccc, ':nv2')


if __name__ == '__main__':
    # python test/normal_case.py -h
    # python test/normal_case.py foo -h
    # python test/normal_case.py foo alpha beta :false
    # python test/normal_case.py foo alpha beta --not-ccc
    cli.run()
