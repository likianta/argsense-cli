from argsense import cli


@cli
def main(greet: bool) -> None:
    """
    params:
        greet (-g):
    """
    print(greet)


if __name__ == '__main__':
    # pox test/false_case_param.py :f
    # pox test/false_case_param.py :false
    # pox test/false_case_param.py --not-greet
    # pox test/false_case_param.py --no-greet
    # pox test/false_case_param.py --!greet
    # pox test/false_case_param.py -G
    cli.run(main)
