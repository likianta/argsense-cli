import lk_logger

lk_logger.setup(quiet=True, show_varnames=True)


def func1(aaa, bbb=None, *ccc, ddd=None, **eee) -> None:
    print(aaa, bbb, ccc, ddd, eee)


def _func2():
    pass


print(':d')
print(':l', __name__, __file__, globals().get('__cli__'))

# pox -m argsense -h
# pox -m argsense run -h
# pox -m argsense run test/non_intrusive.py -h
