from argsense import cli


@cli
def f1(host: str, port: int) -> None:
    """
    params:
        host (-h):
        port (-p):
    """
    print('http://{}:{}'.format(host, port))


@cli
def f2(host: str = '127.0.0.1', port: int = 3000) -> None:
    """
    params:
        host (-h):
        port (-p):
    """
    print('http://{}:{}'.format(host, port))


if __name__ == '__main__':
    # python test/hshort_is_occupied_by_normal_param.py
    # python test/hshort_is_occupied_by_normal_param.py -h
    
    # python test/hshort_is_occupied_by_normal_param.py f1
    # python test/hshort_is_occupied_by_normal_param.py f1 :h
    # python test/hshort_is_occupied_by_normal_param.py f1 :help
    # python test/hshort_is_occupied_by_normal_param.py f1 --help
    # python test/hshort_is_occupied_by_normal_param.py f1 -h
    # python test/hshort_is_occupied_by_normal_param.py f1 -p  # error
    # python test/hshort_is_occupied_by_normal_param.py f1 -h 127.0.0.1  # error
    # python test/hshort_is_occupied_by_normal_param.py f1 -h 127.0.0.1 -p 3000
    
    # python test/hshort_is_occupied_by_normal_param.py f2
    # python test/hshort_is_occupied_by_normal_param.py f2 :h
    # python test/hshort_is_occupied_by_normal_param.py f2 :help
    # python test/hshort_is_occupied_by_normal_param.py f2 --help
    # python test/hshort_is_occupied_by_normal_param.py f2 -h
    # python test/hshort_is_occupied_by_normal_param.py f2 -p  # error
    # python test/hshort_is_occupied_by_normal_param.py f2 -h 127.0.0.1 -p 3000
    cli.run()
