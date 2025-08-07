from argsense import cli


@cli
def main(name: str) -> None:
    print(f'Hello {name}')


if __name__ == '__main__':
    # $env.ARGSENSE_DEBUG = '1'  # optional
    # pox test/func_loop.py Alice :loop
    #   input: Bob
    #   input: Charlie
    #   ...
    #   input: exit
    cli.run(main)
