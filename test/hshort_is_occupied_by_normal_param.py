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
    # pox test/hshort_is_occupied_by_normal_param.py
    # pox test/hshort_is_occupied_by_normal_param.py -h
    
    # pox test/hshort_is_occupied_by_normal_param.py f1
    # pox test/hshort_is_occupied_by_normal_param.py f1 :h
    # pox test/hshort_is_occupied_by_normal_param.py f1 :help
    # pox test/hshort_is_occupied_by_normal_param.py f1 --help
    # pox test/hshort_is_occupied_by_normal_param.py f1 -h
    # pox test/hshort_is_occupied_by_normal_param.py f1 -p  # error
    # pox test/hshort_is_occupied_by_normal_param.py f1 -h 127.0.0.1  # error
    # pox test/hshort_is_occupied_by_normal_param.py f1 -h 127.0.0.1 -p 3000
    
    # pox test/hshort_is_occupied_by_normal_param.py f2
    # pox test/hshort_is_occupied_by_normal_param.py f2 :h
    # pox test/hshort_is_occupied_by_normal_param.py f2 :help
    # pox test/hshort_is_occupied_by_normal_param.py f2 --help
    # pox test/hshort_is_occupied_by_normal_param.py f2 -h
    # pox test/hshort_is_occupied_by_normal_param.py f2 -p  # error
    # pox test/hshort_is_occupied_by_normal_param.py f2 -h 127.0.0.1 -p 3000
    cli.run()
