from argsense import cli


def whois_using_port(
    port: int, preview: bool = True, kill: bool = False
) -> None:
    print(locals())


if __name__ == '__main__':
    cli.run(whois_using_port, mode='tui')
