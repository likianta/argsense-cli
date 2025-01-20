def main(aaa: int, bbb: str, ccc: bool = True):
    print(aaa, bbb, ccc)


print('111')

if __name__ == '__main__':
    # pox -m argsense cli test/run_effect/run_by_argsense_cli.py -h
    # pox -m argsense cli test/run_effect/run_by_argsense_cli.py main 123 abc
    print('222')
