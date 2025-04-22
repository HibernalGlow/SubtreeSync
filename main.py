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
- `--interactive`, `-i`: 使用交互式菜单
"""
    md = Markdown(help_text)
    console.print(Panel(md, title="SubtreeSync 帮助", border_style="green"))

def run_interactive_mode():
    """运行交互式模式"""
    from src.interactive import select_mode, select_repo, confirm_action, show_operation_result, select_repos_for_action
    from src.utils import load_subtree_repos
    
    while True:
        mode = select_mode()
        if mode is None:
            return True
        
        if mode == "add":
            from src.add import add_subtree
            args = argparse.Namespace(remote=None, name=None, prefix=None, branch="main", 
                                     yes=False, no_taskfile=False, interactive=True)
            result = add_subtree(args)
        elif mode == "pull":
            from src.pull import pull_all_subtrees, pull_subtree
            repos = load_subtree_repos()
            
            if not repos:
                show_operation_result(False, "拉取", "没有配置的子树仓库")
                continue
            
            # 支持多选仓库
            selected_repos = select_repos_for_action(repos, "拉取")
            if not selected_repos:
                continue
                
            if len(selected_repos) == 1:
                # 单个仓库
                args = argparse.Namespace(name=selected_repos[0]["name"], yes=False, interactive=True)
                result = pull_subtree(args, selected_repos[0])
            else:
                # 多个仓库
                result = True
                for repo in selected_repos:
                    console.print(f"\n[bold cyan]正在拉取:[/] {repo['name']} ({repo['prefix']})")
                    args = argparse.Namespace(name=repo["name"], yes=True, interactive=True)
                    sub_result = pull_subtree(args, repo)
                    if not sub_result:
                        result = False
                        
        elif mode == "push":
            from src.push import push_all_subtrees, push_subtree
            repos = load_subtree_repos()
            
            if not repos:
                show_operation_result(False, "推送", "没有配置的子树仓库")
                continue
            
            # 支持多选仓库
            selected_repos = select_repos_for_action(repos, "推送")
            if not selected_repos:
                continue
            
            if len(selected_repos) == 1:
                # 单个仓库
                args = argparse.Namespace(name=selected_repos[0]["name"], yes=False, check_changes=True, interactive=True)
                result = push_subtree(args, selected_repos[0])
            else:
                # 多个仓库
                result = True
                for repo in selected_repos:
                    console.print(f"\n[bold cyan]正在推送:[/] {repo['name']} ({repo['prefix']})")
                    args = argparse.Namespace(name=repo["name"], yes=True, check_changes=True, interactive=True)
                    sub_result = push_subtree(args, repo)
                    if not sub_result:
                        result = False
                        
        elif mode == "list":
            from src.list import list_subtrees
            args = argparse.Namespace(verbose=True, interactive=True)
            result = list_subtrees(args)
        else:
            show_operation_result(False, "操作", f"未知模式: {mode}")
            result = False
        
        # 每次操作后暂停
        if input("\n按回车继续..."):
            pass
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Git Subtree 同步工具", add_help=False)
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")
    parser.add_argument("--help", "-h", action="store_true", help="显示帮助信息")
    parser.add_argument("--interactive", "-i", action="store_true", help="使用交互式菜单")
    
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
    add_parser.add_argument("--interactive", "-i", action="store_true", help="使用交互式菜单")
    
    # pull 命令
    pull_parser = subparsers.add_parser("pull", help="拉取子树更新")
    pull_parser.add_argument("--name", help="仓库名称，如不指定则拉取所有")
    pull_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作")
    pull_parser.add_argument("--interactive", "-i", action="store_true", help="使用交互式菜单")
    
    # push 命令
    push_parser = subparsers.add_parser("push", help="推送子树更新")
    push_parser.add_argument("--name", help="仓库名称，如不指定则推送所有")
    push_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作")
    push_parser.add_argument("--check-changes", action="store_true", help="检查是否有更改需要推送")
    push_parser.add_argument("--interactive", "-i", action="store_true", help="使用交互式菜单")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有子树")
    list_parser.add_argument("--verbose", action="store_true", help="显示详细信息")
    list_parser.add_argument("--interactive", "-i", action="store_true", help="使用交互式菜单")
    
    args = parser.parse_args()
    
    # 如果没有参数则进入交互模式
    if len(sys.argv) == 1 or args.interactive:
        return run_interactive_mode()
    
    if args.version:
        print_version()
        return True
    
    if args.help:
        print_help()
        return True
    
    # 添加交互式标志
    if not hasattr(args, 'interactive'):
        args.interactive = False
    
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
    
    return result

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]操作已取消[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]发生错误:[/] {str(e)}")
        sys.exit(1)