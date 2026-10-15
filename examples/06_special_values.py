from argsense import cli


def train(
    count: int,
    addr: int,
    rate: float = 0.1,
    tag: str = '',
    verbose: bool = False,
):
    """
    Train a model.

    Params:
        count: The number of iterations.
        addr: The address to bind, written in hex (e.g. 0xFFFF).
        rate: The learning rate.
        tag: An optional tag. Use ':empty' to pass an empty string.
        verbose: Print more information.
    """
    print(
        'count = {}, addr = {}, rate = {}, tag = {!r}, verbose = {}'.format(
            count, addr, rate, tag, verbose
        )
    )


if __name__ == '__main__':
    # argsense understands a set of special values:
    #
    #   :true   -> True          :t -> True   (alias)
    #   :false  -> False         :f -> False  (alias)
    #   :none   -> None
    #   :empty  -> ''            (an empty string)
    #
    # python examples/06_special_values.py 5 0xFFFF 0.25 abc :true
    # python examples/06_special_values.py --count 5 --addr 0xFFFF --tag abc
    # python examples/06_special_values.py --count 5 --addr 0xFFFF --tag :empty --verbose
    # python examples/06_special_values.py --count 5 --addr 0xFFFF --tag :none
    # python examples/06_special_values.py 0b1111 0xAF2C 0.25 abc :false
    cli.run(train)
