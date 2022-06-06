# Argsense CLI

> The documentation is under construction.

![](.assets/gQqE28Z6lC.png "(outdated)")

![](.assets/20220606164759.jpg "latest")

**argsense** is a command line interface made with Python.

## Usage

```python
from argsense import cli

@cli.cmd
def hello(name: str):
    print(f'Hello {name}!')

if __name__ == '__main__':
    cli.run()
```
