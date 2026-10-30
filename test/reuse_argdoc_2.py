import typing as tp
from argsense import cli


def bump_version(new_version: str = '') -> tp.Tuple[str, str]:
    """
    Args:
        new_version:
            If you just to bump build number, leave `new_version` empty; else -
            pass a semantic version number (in the `<major>.<minor>.<patch>` -
            format) for new version.
            There's no need to care about how does build number is progressed, -
            you should never pass an explicit build number to this function.
            Shorthand: empty pass -> cosmetic bump; explicit pass -> explicit -
            bump.
    """
    return ('', '')


def build_apk(new_version: str = '') -> None:
    """
    Args:
        new_version: See `@bump_version:new_version`.
    """


if __name__ == '__main__':
    # python test/reuse_argdoc_2.py bump_version -h
    # python test/reuse_argdoc_2.py build_apk -h
    cli.run()
