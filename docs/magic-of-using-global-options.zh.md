# 全局变量 `:help` 是如何被传递的

当使用者调用这样一行命令:

```sh
py hello_world.py run -h
```

内部发生了什么?

1. argsense 开始解析参数 (sys.argv)
2. 解析结果简化后的示意结构如下所示:

    ```py
    {
        'args': [],
        'kwargs': {':help': True},
    }
    ```

3. 接着, argsense 会尝试将 args 和 kwargs 传给 hello_world 的 run 函数:

    ```py
    # hello_world.py
    def run(*args, **kwargs):
        print(args, kwargs)

    # argsense internal
    run(*[], **{':help': True})
    ```

    这里有一个比较有意思的地方, 我们会发现:

    ```py
    # 使用 k=v 的方式传递参数, 会报语法错误.
    run(:help=True)
    #   ^ SyntaxError: invalid syntax

    # 但是使用 **kwargs 的方式, 却可以正常运行.
    run(**{':help': True})
    # -> kwargs = {':help': True}
    ```

    这就是为什么 argsense 在传递全局参数时 (一种以 ":" 开头的特殊参数), 不会报错的原因.

## 关联代码

- `argsense/cli.py : class GlobalOptions`
- `argsense/cli.py : def run : code the_bottom_lines`
- `argsense/argparse/parser.py : dict SPECIAL_ARGS`
- `argsense/converter.py : def args_2_cargs`
