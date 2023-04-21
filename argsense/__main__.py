import os
import sys


def run() -> None:
    os.environ['ARGSENSE_TUI'] = '1'
    # print(sys.argv, ':vf2')
    sys.argv.pop(0)
    # print(':f2sl', loads(sys.argv[0], 'plain'))
    with open(sys.argv[0], 'r') as f:
        code = f.read()
    exec(code, {
        '__name__': '__main__',
        '__file__': os.path.abspath(sys.argv[0]),
    })


def help():  # noqa
    pass


if __name__ == '__main__':
    # py -m argsense <target.py>
    # argsense <target.py>
    run()
