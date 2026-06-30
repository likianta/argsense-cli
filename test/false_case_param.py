from argsense import cli


@cli
def main(greet: bool) -> None:
    """
    params:
        greet (-g):
    """
    print(greet)


if __name__ == '__main__':
    # python test/false_case_param.py :f
    # python test/false_case_param.py :false
    # python test/false_case_param.py --not-greet
    # python test/false_case_param.py --no-greet
    # python test/false_case_param.py --!greet
    # python test/false_case_param.py -G
    cli.run(main)
