from argsense import cli


@cli.cmd()
def main(**kwargs):
    print(kwargs)


if __name__ == '__main__':
    cli.run(main)
