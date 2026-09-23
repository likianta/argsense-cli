import neoprint as np
from argsense import cli


@cli
def bar(name: str, debug: bool = False):
    """
    Args:
        name (-n):
        debug (-d):
    """
    np.show(name, debug, ':n')


if __name__ == '__main__':
    # python -m test.run_as_pakcage.foo
    # python -m test.run_as_pakcage.foo -h
    # python -m test.run_as_pakcage.foo Alice -d
    cli.run(bar)
