from argsense import cli


def deploy(alpha: bool = False, beta: str = ''):
    """
    Deploy a build to a channel.

    Params:
        alpha (-a): Whether to deploy to the alpha channel.
        beta (-b): The build label to deploy.
    """
    print('alpha = {}, beta = {!r}'.format(alpha, beta))


if __name__ == '__main__':
    # a short name is an abbreviation of the long option:
    #
    # python examples/04_short_options.py -a
    # python examples/04_short_options.py --alpha
    # python examples/04_short_options.py -b nightly
    # python examples/04_short_options.py --beta nightly
    #
    # the uppercase form of a short flag means "not" (i.e. False):
    #
    # python examples/04_short_options.py -A
    # python examples/04_short_options.py --not-alpha
    cli.run(deploy)
