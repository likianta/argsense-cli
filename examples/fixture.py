import shlex  # a built-in library to split string into command line arguments.
from importlib import import_module

from lk_utils import run_cmd_args

from argsense import cli


@cli.cmd()
def test(file: str, ignore_error=False) -> None:
    """
    args:
        file: a '.py' file. the path should relative to project root. i.e. it -
            should be like 'examples/target.py'.
            in the file, there must be a function named 'test' which yields -
            one or more command line arguments. like below:
            
                # some_test.py
                def test() -> Iterator[str]:
                    yield '-h'
                    yield 'login -h'
                    yield 'login alice'
                    yield 'login alice 123456'
                    yield 'login --name alice'
                    yield 'login --name alice --password 123456'
                    
            each yield represents a command that will be executed.
    
    kwargs:
        ignore_error (-i): if False, the execution will be stopped at the -
            first exception happened command.
            
    note:
        add project root to PYTHONPATH.
        use full screen to see the output. or the character panels will be -
        messed up.
    """
    assert file.startswith('examples/') and file.endswith('.py')
    module = import_module(file.replace('/', '.')[:-3])
    for args in module.test():
        print(':id', 'py {} {}'.format(file, args))
        run_cmd_args('py', file, *shlex.split(args),
                     verbose=True, ignore_error=ignore_error)


@cli.cmd()
def auto_test_all():
    test('examples/classic.py')
    test('examples/advanced.py')
    test('examples/errors.py', ignore_error=True)
    test('examples/seldomly_used.py', ignore_error=True)


if __name__ == '__main__':
    cli.run()
