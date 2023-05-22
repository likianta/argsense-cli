import lk_logger

from argsense import cli

lk_logger.setup(quiet=True)


@cli.cmd()
def main(count=100) -> None:
    print(count)


if __name__ == '__main__':
    cli.run(main)
