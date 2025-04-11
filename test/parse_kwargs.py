from argsense import cli


@cli
def func1(aaa: bool = None, *, bbb: int):
    print(aaa, bbb)


@cli
def func2(aaa: bool = None, *, bbb: int, ccc: str = None):
    print(aaa, bbb, ccc)


@cli
def func3(aaa: bool = None, *, bbb: int, ccc: str = None):
    """
    params:
        aaa (-a):
        bbb (-b):
        ccc (-c):
    """
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    cli.run()
