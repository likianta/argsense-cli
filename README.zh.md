# Argsense | 自动感知的命令行参数解析器

将脚本函数的调用体验无缝迁移到命令行调用.

*before:*

```python
# main.py

def greeting(name: str):
    print(f"Hello, {name}!")

if __name__ == "__main__":
    greeting("Likia")
```

*after:*

```python
# main.py
import argsense

def greeting(name: str):
    print(f"Hello, {name}!")

if __name__ == "__main__":
    argsense.run(greeting)
```

```bash
python3 main.py --help
```

## 设计目标

1. 根据 python 类型注解来判断参数类型
2. 从注释文档中提取帮助信息
3. 美化的命令行界面 (基于 rich)
4. 交互式命令行界面 (基于 textual)
5. 不影响原函数调用

## 开发动机

Q: 为什么有这个项目? 和 argparse, click, typer, fire 相比有什么不同? 

A: 参考这篇 [评测文章](), 该文包含了个人对以上库的理解以及各自的不足之处.
