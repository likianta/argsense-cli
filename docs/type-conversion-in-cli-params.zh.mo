# CLI 传参中的参数类型转换说明

## 尖角标记 `^` 用于自动类型转换

``` :table(simple)

mark        desc
----        ----
^true       python True type
^false      python False type
^none       python None type
^123        force using string type '123'
^^          ^
^(...)      the single quote ('...')
^[...]      the double quote ("...")

```

[**补充说明:]

`^123` 等同于 `^(123)` 或 `^[123]`.

[**实战演示:]

``` :codeblock(py, title=demo.py)
from argsense import cli


def main(*args, **kwargs):
    print(f'{args =}')
    print(f'{kwargs =}')


cli.run(main)
```

``` :codeblock(ps1)

py demo.py aaa bbb ccc
#   args = ('aaa', 'bbb', 'ccc')
#   kwargs = {}

py demo.py 'aaa bbb ccc'
#   args = ('aaa bbb ccc',)
#   kwargs = {}

py demo.py aaa 123
#   args = ('aaa', 123)
#   kwargs = {}

py demo.py aaa ^123
#   args = ('aaa', '123')
#   kwargs = {}

py demo.py ^true ^false ^none
#   args = (True, False, None)
#   kwargs = {}

py demo.py '[123, aaa, ^456, ^true, false]'
#   args = ([123, 'aaa', '456', True, 'false'],)
#   kwargs = {}

py demo.py aaa --mmm 123 --not-nnn
#   args = ('aaa',)
#   kwargs = {'mmm': 123, 'nnn': False}

py demo.py aaa -m 123 -N
#   args = ('aaa',)
#   kwargs = {'m': 123, 'n': False}

py demo.py '{a: aaa, b: 123, c: ^true}'
#   args = ({'a': 'aaa', 'b': 123, 'c': True},)
#   kwargs = {}

```

