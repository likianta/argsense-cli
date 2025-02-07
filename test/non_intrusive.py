import lk_logger

lk_logger.setup(quiet=True, show_varnames=True)


def func1(aaa, bbb=None, *ccc, ddd=None, **eee) -> None:
    print(aaa, bbb, ccc, ddd, eee)


def _func2():
    pass


print(':d')
print(':lv2', {
    '__file__': __file__,
    '__name__': __name__,
    '__cli__': globals().get('__cli__'),
})

# pox -m argsense -h
# pox -m argsense test/non_intrusive.py -h
# pox -m argsense test/non_intrusive.py func1 -h
# pox -m argsense test/non_intrusive.py func1 \
#   alpha beta xyz 123 0xFFFF --ddd eee --fff ggg --hhh :true
