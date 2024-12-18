import lk_logger
lk_logger.setup()

from argsense import cli


@cli.cmd()
def main(aaa: int, bbb: str, *ccc, ddd: bool = True, **eee):
    """
    just print the incoming arguments.
    
    params:
        aaa: million central free if already bill.
        bbb (-b): wait size information policy.
        ccc (-c): short nature day with organization.
        **ddd:
            eee: land course capital about lose.
            fff (-f):
                fight stand high to little leg. yes million consumer number -
                ago financial alone.
    """
    print(aaa, bbb, ccc, ddd, eee)


if __name__ == '__main__':
    # pox test/single_entrance.py -h
    cli.run(main)
