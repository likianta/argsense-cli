"""
A single command with a lot of parameters.

It is used to exercise the scrollable parameter area and the minimum height of
the log panel: the form cannot show all the rows at once, so the parameter area
must scroll while the run buttons and the log panel stay where they are.

Usage:
    python test/tui_test/many_params.py
    python test/tui_test/many_params.py :cli -h
"""

from argsense import cli


def configure(
    project_name: str,
    version: str = '0.1.0',
    author: str = '',
    email: str = '',
    description: str = '',
    license: str = 'MIT',
    python_requires: str = '>=3.9',
    homepage: str = '',
    keywords: str = '',
    package_dir: str = '.',
    output_dir: str = 'dist',
    jobs: int = 4,
    timeout: int = 60,
    retries: int = 2,
    build_wheel: bool = True,
    build_sdist: bool = True,
    clean: bool = True,
    verbose: bool = False,
    dry_run: bool = False,
) -> None:
    """
    A fictional "configure" command with a lot of options.

    Args:
        project_name: The project name.
        version: The project version.
        author: The author name.
        email: The author email.
        description: A one line description.
        license: The license identifier, e.g. "MIT".
        python_requires: The supported python versions.
        homepage: The project homepage.
        keywords: A comma separated keyword list.
        package_dir: Where the package lives.
        output_dir: Where the build artifacts go.
        jobs: How many parallel jobs to use.
        timeout: The network timeout, in seconds.
        retries: How many times to retry on failure.
        build_wheel (-w): Build a wheel.
        build_sdist (-s): Build a source distribution.
        clean (-c): Clean the output directory before building.
        verbose (-v): Print more details.
        dry_run (-n): Do not actually build anything.
    """
    print('configure {} v{}'.format(project_name, version))
    print('  author    : {} <{}>'.format(author or '-', email or '-'))
    print('  license   : {}'.format(license))
    print('  requires  : {}'.format(python_requires))
    print('  output    : {}'.format(output_dir))
    print('  jobs      : {}'.format(jobs))
    print('  build     : wheel={} sdist={}'.format(build_wheel, build_sdist))
    print('  dry run   : {}'.format(dry_run))


if __name__ == '__main__':
    cli.run(configure, mode='tui')
