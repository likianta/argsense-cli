from argsense import argtype
from argsense import cli

class T:
    Name = argtype.Str(
        '''
        Party sure pull both foreign. He small unit guy often north. Total \\
        time any section mouth.
        Themselves far recent get. Local produce single. Sister behavior \\
        benefit then arrive PM amount. Product computer value top style. \\
        Probably land party small again modern deep how.
        Song able democratic enough.
        '''
    )
    Name2 = str

@cli
def foo(name: T.Name):
    pass

@cli
def bar(name: T.Name):
    pass

cli.run()
