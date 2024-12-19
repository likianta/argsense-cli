from argsense import cli


@cli.cmd()
def main(aaa: int, bbb: str, ccc: bool = True):
    """
    just print the incoming arguments.
    
    params:
        aaa: million central free if already bill.
        bbb (-b): wait size information policy.
        ccc (-c): short nature day with organization.
    """
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    # pox test/single_entrance.py -h
    cli.run(main)
