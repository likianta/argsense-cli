
class E:  # Exceptions
    
    class FailedParsingArgv(Exception): ...
    
    class InvalidCommand(Exception): ...


class ArgparsingFailed(Exception):
    """
    accurately report that which element is parsing failed.

    conception:
        input: py test.py foo --bar baz
        report:
            py test.py foo --bar baz
                           ~~~~~
                `--bar` was not recognized as a valid option in `foo` command.
                did you mean "--bart"?
    """
    
    def __init__(self, context):
        pass
