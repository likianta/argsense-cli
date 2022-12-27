from argsense import cli


def test():
    yield 'stagger-color-if-too-many-params -h'


@cli.cmd()
def stagger_color_if_too_many_params(
        apple, banana, orange,
        pear, grape, pineapple,
        monday=1, tuesday=2, wednesday=3,
        thursday=4, friday=5, saturday=6, sunday=7
):
    print(apple, banana, orange, pear, grape, pineapple)
    print(monday, tuesday, wednesday, thursday, friday, saturday, sunday)


if __name__ == '__main__':
    cli.run()
