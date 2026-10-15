from argsense import cli


def do_something(do_it: bool = True):
    """
    Do something, or do not.

    Params:
        do_it (-d): Whether to actually do it.
    """
    print('do it' if do_it else 'do not do it')


if __name__ == '__main__':
    # a bool parameter is a "flag": giving the option alone already means True.
    #
    # python examples/05_flags.py --do-it
    # python examples/05_flags.py -d
    #
    # the negated forms all mean False:
    #
    # python examples/05_flags.py --not-do-it
    # python examples/05_flags.py --no-do-it
    # python examples/05_flags.py --!do-it
    # python examples/05_flags.py -D
    #
    # an explicit special value works as well (see 06_special_values.py):
    #
    # python examples/05_flags.py :true
    # python examples/05_flags.py :false
    cli.run(do_something)
