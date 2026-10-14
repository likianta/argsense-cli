# AGENTS.md

> 本文件面向 AI 编码助手与项目贡献者, 用于快速了解 argsense-cli 的结构, 约定与工作方式.

## 项目简介

argsense 是一个基于 [Rich](https://github.com/Textualize/rich) 的 Python 命令行接口 (CLI) 工具库. 它对 `sys.argv` 做高级封装: 只要给函数加上装饰器, 就能从 **函数签名 + 注释文档** 自动生成命令行参数解析与帮助界面.

## 环境与依赖

- 依赖声明在 `pyproject.toml`
- 项目使用 uv 管理环境, 使用 ruff 格式化代码, 使用 ty 进行静态类型检查. 具体规则配置在 `pyproject.toml`

## 目录结构

```
argsense-cli/
├── argsense/                 # 源码包
│   ├── __init__.py           # 对外导出的公共 API
│   ├── __main__.py           # `python -m argsense <target>` 入口 (cli / tui / gui)
│   ├── cli.py                # CommandLineInterface: 命令注册, 运行, docstring 引用解析
│   ├── config.py             # 全局配置项
│   ├── converter.py          # 名称/类型转换
│   ├── parser/               # 解析层
│   │   ├── func_parser.py    # parse_function(): 解析函数签名 (FuncInfo)
│   │   ├── docs_parser.py    # parse_docstring(): 解析 docstring
│   │   └── args_parser/      # parse_argv(): 把 argv 解析成实参
│   └── renderer/             # 渲染层 (rich 帮助界面; psg 为 PySimpleGUI 图形界面后端)
├── test/                     # 手工运行的测试脚本 (非 pytest), 部分测试可能过时, 注意甄别
├── docs/                     # 补充文档 (部分可能已过时)
├── .assets/                  # 文档资源所使用到的插图保存在这里
├── README.md                 # 自述文档
└── CHANGELOG.zh.md           # 更新日志
```

## 代码风格

- 优先使用 `format` 而不是 `f-string`.
- 代码中使用全英文, 不要有中文注释.
- 不需要在入口脚本的顶部添加 `sys.path.append(...)`. 因为我们已经设置好了环境变量 (`PYTHONPATH=.;src;lib;.venv/Lib/site-packages`).
- ruff: 行宽 80; 字符串用单引号.
- isort: 每行一个导入语句; 相对导入排序由近及远 (. -> .. -> ...).
- 每当完成修改后, 使用 `ty check`, `ruff check`, `ruff format` 等命令检查代码风格.

## 核心架构

解析与渲染的主链路如下:

1. **解析阶段**
   - `parse_function(...)` → 得到 `FuncInfo` (参数名, 类型, 默认值等)
   - `parse_docstring(...)` → 得到描述信息
   - `func_info.fill_docs_info(...)` → 把描述回填到 `FuncInfo`
2. **注册阶段** (`cli.py`)
   - `@cli` 装饰器 → `CommandLineInterface.add_cmd()` 注册命令
3. **运行阶段** (`cli.py`)
   - `cli.run()` / `cli.exec_argv()` → 交给 `parser/args_parser` 解析 argv, 再调用目标函数
   - `exec_argv()` 入口会先调用 `resolve_doc_references()`, 解析 docstring 中的参数引用 (见下)
4. **渲染阶段** (`renderer/rich`)
   - 生成帮助界面, 参数表格, 错误提示

**内置命令**: `-h` / `:help` 显示帮助; `:loop` 进入循环调用模式; `:true` `:false` `:none` `:empty` 为特殊值 (详见 README).

## Docstring 格式约定

参数说明写在 `params:` 段中, 基本格式:

```
<param_name> (<short_name>): <first_line_of_description>
    <more_description_lines>
```

详见 `docs/how-to-parse-docstring.zh.md` 及 README 的 "In-Depth Reading" 章节.
