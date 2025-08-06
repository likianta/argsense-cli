from argsense import cli


@cli
def main(name):
    print(f'Hello {name}')


if __name__ == '__main__':
    # $env.ARGSENSE_DEBUG = '1'
    # pox test/interactive.py Alice :i
    cli.run(main)
