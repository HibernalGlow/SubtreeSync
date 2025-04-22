#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 同步工具 - 主入口
集成添加、拉取和推送功能
"""

import sys
import argparse
from pathlib import Path

# 确保当前目录在 Python 路径中，以便能够导入模块
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
except ImportError:
    print("请先安装Rich库: pip install rich")
    print("命令: pip install rich")
    sys.exit(1)

# 创建Rich控制台对象
console = Console()

def print_version():
    """打印版本信息"""
    from src import __version__
    console.print(f"SubtreeSync v{__version__}", style="bold green")

def print_help():
    """打印帮助信息"""
    help_text = """
# SubtreeSync 使用帮助

## 简介

SubtreeSync 是一个 Git Subtree 管理工具，用于简化 Git Subtree 操作。

## 命令

### 添加子树

```bash
python subtree-sync.py add
```

交互式添加一个新的 Git Subtree。

### 拉取更新

```bash
python subtree-sync.py pull [--name REPO_NAME]
```

拉取所有或指定仓库的更新。

### 推送更新

```bash
python subtree-sync.py push [--name REPO_NAME]
```

推送本地更改到所有或指定的远程仓库。

### 列出子树

```bash
python subtree-sync.py list
```

列出所有已配置的 Git Subtree。

## 选项

- `--help`, `-h`: 显示帮助信息
- `--version`, `-v`: 显示版本信息
- `--yes`, `-y`: 自动确认所有操作
- `--verbose`: 显示详细信息
"""
    md = Markdown(help_text)
    console.print(Panel(md, title="SubtreeSync 帮助", border_style="green"))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Git Subtree 同步工具", add_help=False)
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")
    parser.add_argument("--help", "-h", action="store_true", help="显示帮助信息")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # add 命令
    add_parser = subparsers.add_parser("add", help="添加一个新的 Git Subtree")
    add_parser.add_argument("--remote", help="远程仓库地址")
    add_parser.add_argument("--name", help="本地仓库名称")
    add_parser.add_argument("--prefix", help="本地目录前缀")
    add_parser.add_argument("--branch", default="main", help="分支名称，默认为 main")
    add_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作")
    add_parser.add_argument("--no-taskfile", action="store_true", help="不添加到 Taskfile.yml")
    
    # pull 命令
    pull_parser = subparsers.add_parser("pull", help="拉取子树更新")
    pull_parser.add_argument("--name", help="仓库名称，如不指定则拉取所有")
    pull_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作")
    
    # push 命令
    push_parser = subparsers.add_parser("push", help="推送子树更新")
    push_parser.add_argument("--name", help="仓库名称，如不指定则推送所有")
    push_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作")
    push_parser.add_argument("--check-changes", action="store_true", help="检查是否有更改需要推送")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有子树")
    list_parser.add_argument("--verbose", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    
    if args.version:
        print_version()
        return 0
    
    if args.help or len(sys.argv) == 1:
        print_help()
        return 0
    
    # 根据子命令执行不同的功能
    if args.command == "add":
        from src.add import add_subtree
        result = add_subtree(args)
    elif args.command == "pull":
        from src.pull import pull_all_subtrees
        result = pull_all_subtrees(args)
    elif args.command == "push":
        from src.push import push_all_subtrees
        result = push_all_subtrees(args)
    elif args.command == "list":
        from src.list import list_subtrees
        result = list_subtrees(args)
    else:
        console.print("[bold red]错误:[/] 未知命令")
        print_help()
        result = False
    
    return 0 if result else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]操作已取消[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]发生错误:[/] {str(e)}")
        sys.exit(1)