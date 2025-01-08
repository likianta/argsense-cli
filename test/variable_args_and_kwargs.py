from argsense import cli


@cli.cmd()
def func1(aaa: int, *args) -> None:
    """
    whether go avoid player available nothing. it executive box already lose -
    serious.
    indicate unit must industry class score west. draw interest nature week.
    between quality society might. difficult near general evidence people -
    certainly.

    params:
        aaa: million central free if already bill.
        *args: wait size information policy.
    """
    print(aaa, args)


@cli.cmd()
def func2(aaa: int, **kwargs) -> None:
    """
    true identify nor mouth law. process former nothing. left could thought.
    discussion type year recent always gun. brother cost girl. actually big -
    believe relate real. central read one big western.
    spring fine sell thus natural. few message effort say position beyond -
    accept.
    
    params:
        aaa: million central free if already bill.
        **kwargs:
            bbb: land course capital about lose.
            ccc (-c):
                fight stand high to little leg. yes million consumer number -
                ago financial alone.
    """
    print(aaa, kwargs)


@cli.cmd()
def func3(aaa: int, *args, bbb: str = 'ccc', **kwargs) -> None:
    """
    i detail appear fire easy international. society hard probably thus act. -
    use head learn central break.
    leave body pay rest foreign beat. five ball skill perhaps.
    road population have consumer remain wrong pass. certain ground physical. -
    chair although measure travel research thought political.
    
    params:
        aaa: million central free if already bill.
        **kwargs:
            bbb: land course capital about lose.
            ccc (-c):
                fight stand high to little leg. yes million consumer number -
                ago financial alone.
    """
    print(aaa, bbb, args, kwargs)


@cli.cmd()
def func4(aaa, bbb=None, *ccc):
    """
    param `bbb` should be appeared in front of `*ccc`.
    """
    print(aaa, bbb, ccc)


if __name__ == '__main__':
    # pox test/variable_args_and_kwargs.py -h
    # pox test/variable_args_and_kwargs.py func1 -h
    # pox test/variable_args_and_kwargs.py func2 -h
    # pox test/variable_args_and_kwargs.py func3 -h
    cli.run()
