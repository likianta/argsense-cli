from argsense import cli
from typing import Optional
from neoprint import print


@cli
def varkw(**kwargs):
    """
    related:
        - /argsense/config.py : HIDE_UNSTATED_VARIABLE_KWARGS
        - /argsense/renderer/rich/render.py : render_function_parameters()
    """
    print(kwargs, ':l')


@cli
def func1(aaa: Optional[bool] = None, *, bbb: int):
    print(aaa, bbb, ':n')


@cli
def func2(aaa: Optional[bool] = None, *, bbb: int, ccc: Optional[str] = None):
    print(aaa, bbb, ccc, ':n')


@cli
def func3(aaa: Optional[bool] = None, *, bbb: int, ccc: Optional[str] = None):
    """
    params:
        aaa (-a):
        bbb (-b):
        ccc (-c):
    """
    print(aaa, bbb, ccc, ':nv2')


if __name__ == '__main__':
    # py test/parse_kwargs.py -h
    # py test/parse_kwargs.py varkw --aaa Alpha --bbb Beta --ccc :true --ddd 123
    cli.run()
