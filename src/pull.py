#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 拉取更新功能
实现从远程仓库拉取子树更新
"""

import sys
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

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

def pull_subtree(repo_info: Dict[str, Any], args=None) -> bool:
    """
    拉取单个子树的更新
    :param repo_info: 仓库配置信息
    :param args: 命令行参数
    :return: 操作是否成功
    """
    name = repo_info.get("name", "")
    remote = repo_info.get("remote", "")
    prefix = repo_info.get("prefix", "")
    branch = repo_info.get("branch", "main")
    
    console.print(f"\n[bold blue]从 {name} 拉取更新到 {prefix}[/]")
    
    # 构建 git subtree pull 命令
    cmd = ["git", "subtree", "pull", f"--prefix={prefix}", name, branch, "--squash"]
    
    # 显示完整命令
    cmd_str = " ".join(cmd)
    console.print(Panel(Syntax(cmd_str, "bash", theme="monokai"), 
                       title="Git Pull 命令", 
                       border_style="blue"))
    
    success, output = run_command(cmd)
    
    if success:
        console.print(f"[bold green]从 {name} 成功拉取更新![/]")
        console.print(Panel(output.strip(), border_style="green", title="命令输出"))
        
        # 检查是否有更改
        if "Already up to date" in output:
            console.print(f"[yellow]提示:[/] {prefix} 目录已是最新状态，无需更新")
        
        return True
    else:
        console.print(f"[bold red]从 {name} 拉取更新失败:[/]")
        console.print(Panel(output.strip(), border_style="red", title="错误输出"))
        
        # 检查是否因为冲突而失败
        if "conflict" in output.lower():
            console.print("[bold yellow]原因:[/] 拉取过程中出现冲突，请手动解决冲突")
            console.print("[cyan]提示:[/] 可以使用以下命令查看冲突文件:")
            console.print("[dim]    $ git status[/]")
        
        return False

def pull_all_subtrees(args=None) -> bool:
    """
    交互式拉取所有子树更新
    :param args: 命令行参数
    :return: 操作是否成功
    """
    console.print(Panel.fit("[bold green]Git Subtree 拉取更新工具", 
                           border_style="green", 
                           title="GlowToolBox", 
                           subtitle="v1.0"))
    
    # 检查是否在git仓库中
    if not validate_git_repo():
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    if check_working_tree():
        console.print("[bold yellow]警告:[/] 检测到工作区有未提交的更改。建议先提交或暂存这些更改。")
        if not Confirm.ask("是否继续操作?", default=False):
            console.print("操作已取消", style="yellow")
            return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[bold yellow]警告:[/] 没有找到已配置的subtree仓库")
        return False
    
    # 显示将要拉取更新的仓库列表
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
    
    # 如果指定了仓库名，则只拉取特定仓库
    selected_repos = repos
    if args and args.name:
        selected_repos = [repo for repo in repos if repo.get("name") == args.name]
        if not selected_repos:
            console.print(f"[bold red]错误:[/] 找不到名称为 '{args.name}' 的仓库")
            return False
    
    # 确认操作
    if not args or not args.yes:
        if not Confirm.ask(f"\n是否拉取所有显示的 {len(selected_repos)} 个仓库的更新?"):
            console.print("操作已取消", style="yellow")
            return False
    
    # 执行拉取操作
    success_count = 0
    fail_count = 0
    
    for repo in selected_repos:
        if pull_subtree(repo, args):
            success_count += 1
        else:
            fail_count += 1
    
    # 打印操作结果摘要
    console.print("\n[bold]===操作结果摘要===", style="cyan")
    console.print(f"• 总共尝试拉取: [bold]{len(selected_repos)}[/] 个仓库")
    console.print(f"• 成功拉取: [bold green]{success_count}[/] 个仓库")
    if fail_count > 0:
        console.print(f"• 失败: [bold red]{fail_count}[/] 个仓库")
    
    return fail_count == 0