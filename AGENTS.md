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
│   ├── tui.py                # TuiInterface: cli 接口的文本界面 (TUI) 形态
│   ├── parser/               # 解析层
│   │   ├── func_parser.py    # parse_function(): 解析函数签名 (FuncInfo)
│   │   ├── docs_parser.py    # parse_docstring(): 解析 docstring
│   │   └── args_parser/      # parse_argv(): 把 argv 解析成实参
│   └── renderer/             # 渲染层
│       ├── rich/             # 命令行帮助界面 (palette.py 为配色表)
│       ├── tui/              # 文本界面 (Textual; app.py 为表单应用)
│       └── psg/              # PySimpleGUI 图形界面后端
├── sidework/                 # 辅助脚本 (文档插图生成等)
│   ├── readme_screenshots.py # 批量生成 README 插图
│   ├── readme_scenes.py      # README 插图的场景定义 (console scene / tui scene)
│   ├── record_help_interface.py    # 单张帮助界面截图的底层入口
│   └── screenshot_console_output.py # 单个控制台会话截图的底层入口
├── examples/                 # 示例脚本
├── test/                     # 手工运行的测试脚本 (非 pytest), 部分测试可能过时, 注意甄别
│   └── tui_test/             # TUI 的场景脚本与无头测试
├── docs/                     # 补充文档 (部分可能已过时)
│   └── images/               # 文档所使用到的插图 (由 sidework 脚本生成)
├── README.md                 # 自述文档
└── CHANGELOG.md              # 更新日志 (只维护英文版)
```

## 代码风格

- 优先使用 `format` 而不是 `f-string`.
- 代码中使用全英文, 不要有中文注释.
- 不需要在入口脚本的顶部添加 `sys.path.append(...)`. 因为我们已经设置好了环境变量 (`PYTHONPATH=.;src;lib;.venv/Lib/site-packages`).
- ruff: 行宽 80; 字符串用单引号.
- isort: 每行一个导入语句; 相对导入排序由近及远 (. -> .. -> ...).
- 每当完成修改后, 使用 `ty check`, `ruff check`, `ruff format` 等命令检查代码风格.

## 代码提交

如果涉及到文件改动, 并且产生 git 差异, 则在回复的末尾给我提供一个 commit 信息参考 (不要自己提交, 我会复制这个信息然后手动提交).

Commit 信息格式: 

```
<tag>: <message>
```

`<tag>` 有以下类型:

- chore
- del
- doc
- feat
- fix
- refactor
- update

`<message>` 格式要求: 英文, 全小写字符, 建议在 50 字符以内, 如果改动过多导致信息过多, 可以省略不重要的内容. 参考我最近几次历史提交信息文本风格.

如果只修改了 .gitignore 中的文件, 没有产生 git 差异, 则不需要提供 commit 信息参考.

## 文档与插图

- `README.md` 是唯一维护的自述文档 (英文). 更新日志只维护英文版 `CHANGELOG.md`, 中文版已废弃.
- `README.md` 中的插图由 `sidework/readme_screenshots.py` 批量生成, 场景定义在 `sidework/readme_scenes.py`:

  ```shell
  python sidework/readme_screenshots.py            # 刷新全部插图
  python sidework/readme_screenshots.py tui-log    # 只刷新某一张 (逗号分隔可指定多张)
  ```

  其中两类插图: 控制台插图 (模拟终端会话, 或渲染 `-h` 帮助界面), 以及 TUI 插图 (用 `Pilot` 无头驱动 Textual 表单, 再导出截图). 少数插图 (如 `261015-140133`, `261015-140405`, `261015-132007`) 直接运行 `test/` 下的场景脚本.
- 图片名是稳定的 (不带时间戳), 所以刷新插图不会产生孤儿文件; README 通过图片名引用插图.
- 新增或修改 README 插图时, 必须同步更新 `readme_scenes.py` 与 `readme_screenshots.py` 中的清单, 以确保插图始终可重现.
- `sidework/record_help_interface.py` 与 `sidework/screenshot_console_output.py` 是底层录制工具的单独入口; 日常刷新插图直接用 `readme_screenshots.py` 即可.

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
4. **渲染阶段** (两种形态)
   - `renderer/rich`: 生成帮助界面, 参数表格, 错误提示
   - `renderer/tui`: 用 Textual 把命令渲染成可填写的表单 (`mode='tui'`, 或命令行里的 `:tui` / `:itui`)

**内置命令**: `-h` / `:help` 显示帮助; `:loop` 进入循环调用模式; `:true` `:false` `:none` `:empty` 为特殊值 (详见 README).

## Docstring 格式约定

参数说明写在 `params:` 段中, 基本格式:

```
<param_name> (<short_name>): <first_line_of_description>
    <more_description_lines>
```

详见 `docs/how-to-parse-docstring.zh.md` 及 README 的 "In-Depth Reading" 章节.
