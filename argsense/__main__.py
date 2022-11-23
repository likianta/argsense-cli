from .cli import cli


@cli.cmd()
def parse_argstring(argstring: str) -> None:
    from .argparse import parse_argstring
    print(parse_argstring(argstring))
    
    
@cli.cmd(transport_help=True)
def run(*args, **kwargs):
    target = args[0]
    args = args[1:]


if __name__ == '__main__':
    cli.run()
