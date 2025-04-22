#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 推送功能
实现将本地子树的更改推送到远程仓库
"""

import sys
import subprocess
from typing import Dict, List, Optional, Any, Union

try:
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.progress import Progress
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

from .utils import (
    console, run_command, validate_git_repo, check_working_tree,
    load_subtree_repos
)

def has_local_changes(prefix: str) -> bool:
    """
    检查子树是否有本地未推送的更改
    :param prefix: 子树本地目录前缀
    :return: 是否有本地更改
    """
    try:
        # 获取最新提交信息
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s", "--", prefix],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except Exception:
        return False

def push_subtree(args=None, repo_info: Dict[str, Any] = None) -> bool:
    """
    推送单个子树的更新到远程
    :param args: 命令行参数
    :param repo_info: 仓库配置信息
    :return: 操作是否成功
    """
    # 确保repo_info是有效的
    if not repo_info:
        if not args or not getattr(args, "name", None):
            console.print("[bold red]错误:[/] 没有指定仓库信息或名称")
            return False
            
        # 尝试通过名称查找仓库信息
        from .utils import find_repo_by_name
        repo_name = args.name
        repo_info = find_repo_by_name(repo_name)
        if not repo_info:
            console.print(f"[bold red]错误:[/] 找不到名称为 '{repo_name}' 的仓库")
            return False
    
    name = repo_info.get("name", "")
    remote = repo_info.get("remote", "")
    prefix = repo_info.get("prefix", "")
    branch = repo_info.get("branch", "main")
    
    console.print(f"\n[bold blue]将 {prefix} 的更改推送到 {name}[/]")
    
    # 如果指定了检查更改选项，先检查是否有更改要推送
    if args and getattr(args, "check_changes", False):
        if not has_local_changes(prefix):
            console.print(f"[yellow]提示:[/] {prefix} 目录没有检测到需要推送的更改，跳过")
            return True
    
    # 构建 git subtree push 命令
    cmd = ["git", "subtree", "push", f"--prefix={prefix}", name, branch]
    
    # 显示完整命令
    cmd_str = " ".join(cmd)
    console.print(Panel(Syntax(cmd_str, "bash", theme="monokai"), 
                       title="Git Push 命令", 
                       border_style="blue"))
    
    # 执行命令，结果会直接显示在控制台
    success, _ = run_command(cmd)
    
    if success:
        console.print(f"[bold green]成功将 {prefix} 的更改推送到 {name}![/]")
        return True
    else:
        console.print(f"[bold red]推送 {prefix} 的更改到 {name} 失败[/]")
        console.print("[cyan]提示:[/] 如果是权限问题，请确认是否有远程仓库的写入权限")
        console.print("       如果是冲突问题，可能需要先拉取远程更新")
        return False

def push_all_subtrees(args=None) -> bool:
    """
    交互式推送所有子树更新
    :param args: 命令行参数
    :return: 操作是否成功
    """
    console.print(Panel.fit("[bold green]Git Subtree 推送更新工具", 
                           border_style="green", 
                           title="GlowToolBox", 
                           subtitle="v1.0"))
    
    # 检查是否在git仓库中
    if not validate_git_repo():
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    if check_working_tree():
        console.print("[bold yellow]警告:[/] 检测到工作区有未提交的更改。在推送之前，请先提交这些更改。")
        console.print("[cyan]提示:[/] 使用 'git add .' 和 'git commit' 来提交更改")
        return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[bold yellow]警告:[/] 没有找到已配置的subtree仓库")
        return False
    
    # 显示将要推送更新的仓库列表
    console.print("\n[bold]已配置的subtree仓库:[/]")
    table = Table(show_header=True)
    table.add_column("#", style="dim")
    table.add_column("仓库名", style="cyan")
    table.add_column("远程地址", style="green")
    table.add_column("分支", style="blue")
    table.add_column("本地路径", style="yellow")
    
    for i, repo in enumerate(repos):
        table.add_row(
            str(i + 1),
            repo.get("name", ""),
            repo.get("remote", ""),
            repo.get("branch", "main"),
            repo.get("prefix", "")
        )
    
    console.print(table)
    
    # 如果指定了仓库名，则只推送特定仓库
    selected_repos = repos
    if args and args.name:
        selected_repos = [repo for repo in repos if repo.get("name") == args.name]
        if not selected_repos:
            console.print(f"[bold red]错误:[/] 找不到名称为 '{args.name}' 的仓库")
            return False
    
    # 确认操作
    if not args or not args.yes:
        if not Confirm.ask(f"\n是否推送所有显示的 {len(selected_repos)} 个仓库的更改?"):
            console.print("操作已取消", style="yellow")
            return False
    
    # 执行推送操作
    success_count = 0
    fail_count = 0
    
    for repo in selected_repos:
        if push_subtree(repo, args):
            success_count += 1
        else:
            fail_count += 1
    
    # 打印操作结果摘要
    console.print("\n[bold]===操作结果摘要===", style="cyan")
    console.print(f"• 总共尝试推送: [bold]{len(selected_repos)}[/] 个仓库")
    console.print(f"• 成功推送: [bold green]{success_count}[/] 个仓库")
    if fail_count > 0:
        console.print(f"• 失败: [bold red]{fail_count}[/] 个仓库")
    
    return fail_count == 0