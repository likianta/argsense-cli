# 我们是如何解析 docstring 的

*TODO: 待整理*

- 以 args 开头的块是位置参数的说明
- 以 kwargs 开头的块是可选参数的说明
- kwargs 也可以合并到 args 块中

### 如何换行和连接下一行

- 直接回车就是换行. 不需要在两行之间插入空行.
- 有多少行, 就会被渲染为多少行; 空行也不例外 (有多少空行, 就会被渲染为多少空行). 但头部和尾部多余的空行除外 (它们会被去除).
- 如果在 docstring 中因为宽度限制而折行, 但不希望在 CLI 中也显示为换行 -- 也就是我们想要 "连接下一行", 请使用下面的语法:

    1. 在第一行的末尾加一个 " -".
        1. 注意连字符的左侧必须有一个空格.
        2. 连字符右侧可以有零到多个空格, 不影响解析 (解析时会忽略).
        3. 如果连字符左侧有一个以上的空格, 则会保留 (n - 1) 个.
    2. 在第二行保持和第一行相同的缩进.

    这样, 解析器会将这两行连接在一起, 作为一行渲染到 CLI 中.

### 别名

为了让书写保持美观, 我们给 args 和 kwargs 增加了别名.

args 别名:

- arguments
- params

kwargs 别名:

- opts
- options

### 头部描述被截断

只有 args/kwargs 之前的文本会被记录为头部描述, 之后的文本会被忽略.

如下示例, 只有 "calculate the sum of a, b, c." 被记录为头部描述:

```python
def foo(a, b, c):
    """
    calculate the sum of a, b, c.

    args:
        a: ...
        b: ...
        c: ...

    note that a, b, c should be valid number.

    warning:
        make sure they are all non-negative.
    """
    assert a >= 0 and b >= 0 and c >= 0
    return a + b + c
```
