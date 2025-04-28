#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 推送功能
实现将本地子树的更改推送到远程仓库
"""

import sys
import os
import subprocess
from typing import Dict, List, Optional, Any, Union, Tuple

try:
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

from .console import console  # 导入共享的控制台实例
from .interactive import confirm_action
from .utils import load_subtree_repos, find_repo_by_name, run_command
from .split import (
    split_subtree, run_git_command  # 复用split.py中的函数
)

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
        repo_name = args.name
        repo_info = find_repo_by_name(repo_name)
        if not repo_info:
            console.print(f"[bold red]错误:[/] 找不到名称为 '{repo_name}' 的仓库")
            return False
    
    name = repo_info.get("name", "")
    remote = repo_info.get("remote", "")
    prefix = repo_info.get("prefix", "")
    branch = repo_info.get("branch", "main")
    # 获取固定的 split_branch 名称
    split_branch = repo_info.get("split_branch") 
    
    if not split_branch:
        console.print(f"[bold red]错误:[/] 仓库 '{name}' 的配置中缺少 'split_branch' 定义")
        return False

    console.print(f"\n将 {prefix} 的更改推送到 {name} (远程分支: {branch}, 使用 split 分支: {split_branch})")
    
    # 检查是否需要先执行split操作 (默认为 True)
    # 询问用户是否需要先执行 split 操作
    perform_split = False
    if not args or not getattr(args, "yes", False): # 如果不是自动确认模式
        perform_split = Confirm.ask(
            f"\n是否在推送前执行 split 操作以更新本地分支 '{split_branch}'?",
            default=False # 默认不执行
        )
    elif getattr(args, "force_split", False): # 兼容旧的 force_split 参数，如果存在且为True，则执行
        perform_split = True
        console.print("[yellow]检测到 --force-split 参数，将执行 split 操作...[/]")


    if perform_split:
        console.print(f"[yellow]准备执行 split 操作以更新分支 {split_branch}...[/]")
        # 执行split操作，使用固定的分支名
        if not split_subtree(args, repo_info):
            console.print("[bold red]Split 操作失败，无法继续推送[/]")
            return False
        else:
            console.print(f"[bold green]Split 操作完成，分支 {split_branch} 已更新，准备推送...[/]")
    else:
         console.print(f"[yellow]跳过 split 操作，将直接尝试推送分支 {split_branch}[/]")


    # 构建 git subtree push 命令列表
    # 命令格式: git subtree push --prefix=<prefix> <remote_repository> <local_split_branch>:<remote_target_branch>
    # 注意：subtree push 不直接使用 --prefix，而是通过 split 分支来推送
    # 正确的命令应该是: git push <remote_repository> <local_split_branch>:<remote_target_branch>
    # 或者是 git subtree push <remote_name_in_git_config> <local_split_branch>:<remote_target_branch>
    # 但更常见且推荐的是直接用 git push 推送 split 出来的分支
    
    # 使用 git push 推送 split 分支
    cmd_list = ["push", remote, f"{split_branch}:{branch}"]

    # 显示完整命令
    cmd_str = " ".join(['git'] + cmd_list)
    console.print("\n[bold yellow]--- Git Push 命令 ---[/]")
    console.print(cmd_str)
    console.print("[bold yellow]---------------------[/]")

    # 执行命令
    from .utils import run_git_command_direct
    success = run_git_command_direct(cmd_list)

    if success:
        console.print(f"\n[bold green]成功将 {split_branch} 推送到 {remote} 的 {branch} 分支![/]")
        return True
    else:
        console.print(f"\n[bold red]推送 {split_branch} 到 {remote} 的 {branch} 分支失败[/]")
        console.print("[yellow]提示:[/] 如果是权限问题，请确认是否有远程仓库的写入权限")
        console.print("      如果是冲突问题(non-fast-forward)，可能需要先拉取远程更新到主仓库，然后重新 split 和 push")
        return False

def push_all_subtrees(args=None) -> bool:
    """
    交互式推送所有子树更新
    :param args: 命令行参数
    :return: 操作是否成功
    """
    console.print("\n[bold cyan]--- Git Subtree 推送更新工具 ---[/]")
    
    # 检查是否在git仓库中
    success, _ = run_git_command(["rev-parse", "--is-inside-work-tree"], False)
    if not success:
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    success, output = run_git_command(["status", "--porcelain"], False)
    if success and output.strip():
        console.print("[bold yellow]警告:[/] 检测到工作区有未提交的更改。在推送之前，请先提交这些更改。")
        console.print("[yellow]提示:[/] 使用 'git add .' 和 'git commit' 来提交更改")
        return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[bold yellow]警告:[/] 没有找到已配置的subtree仓库")
        return False
    
    # 显示将要推送更新的仓库列表
    console.print("\n已配置的subtree仓库:")
    table = Table(show_header=True)
    table.add_column("#", style="dim")
    table.add_column("仓库名", style="cyan")
    table.add_column("远程地址", style="green")
    table.add_column("分支", style="blue")
    table.add_column("Split分支", style="magenta")
    table.add_column("本地路径", style="yellow")
    
    for i, repo in enumerate(repos):
        repo_name = repo.get("name", "")
        # 从 repo_info 获取 split_branch
        split_branch = repo.get("split_branch", "[未定义]") 
        table.add_row(
            str(i + 1),
            repo_name,
            repo.get("remote", ""),
            repo.get("branch", "main"),
            split_branch, # 显示固定的 split_branch
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
    if not args or not getattr(args, "yes", False):
        if not Confirm.ask(f"\n是否推送所有显示的 {len(selected_repos)} 个仓库的更改?"):
            console.print("[yellow]操作已取消[/]")
            return False
    
    # 执行推送操作
    success_count = 0
    fail_count = 0
    
    for repo in selected_repos:
        if push_subtree(args, repo):
            success_count += 1
        else:
            fail_count += 1
    
    # 打印操作结果摘要
    console.print("\n[bold cyan]===操作结果摘要===[/]")
    console.print(f"• 总共尝试推送: {len(selected_repos)} 个仓库")
    console.print(f"• 成功推送: {success_count} 个仓库")
    if fail_count > 0:
        console.print(f"• 失败: {fail_count} 个仓库")
    
    return fail_count == 0