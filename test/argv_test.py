from argsense import cli


def foo(func):
    func()


def bar(host: str, port: int = 8080):
    """
    a demo function that prints the host and port.

    params:
        host: the host address.
        port (-p): the port number.
    """
    print(host, port)


if __name__ == '__main__':
    # positive tests:
    #   python test/argv_test.py 127.0.0.1
    #       -> 127.0.0.1 8080
    #   python test/argv_test.py 127.0.0.1 8080
    #       -> 127.0.0.1 8080
    #   python test/argv_test.py 127.0.0.1 -p 8080
    #       -> 127.0.0.1 8080
    #   python test/argv_test.py --host 127.0.0.1 --port 8080
    #       -> 127.0.0.1 8080
    #   python test/argv_test.py -h
    #       -> render the help interface (the function is not called)
    #
    # negative tests (report an error and exit with code 1):
    #   python test/argv_test.py
    #       error: host is required
    #   python test/argv_test.py 127.0.0.1 baz
    #       error: baz is not a valid port
    foo(cli.wrap(bar))
