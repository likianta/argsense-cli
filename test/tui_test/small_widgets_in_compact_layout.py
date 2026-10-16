from argsense import cli
from typing import Optional


def whois_using_port(
    port: int, preview: Optional[bool] = None, kill: bool = False
) -> None:
    print(locals())


if __name__ == '__main__':
    cli.run(whois_using_port, mode='tui')
