#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree Split功能
实现将本地子树目录分离为独立分支，为推送做准备
"""

import sys
import subprocess
import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.progress import Progress
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

import git  # Import GitPython
from .interactive import confirm_action
from .utils import (
    validate_git_repo, check_working_tree,
    load_subtree_repos,
    get_repo, run_git_command_stream
)

# 创建Rich控制台对象
console = Console()

def get_split_branch_name(repo_name: str) -> str:
    """
    根据仓库名生成split分支名，格式为"仓库名#ST日期"
    
    :param repo_name: 仓库名称
    :return: 生成的分支名
    """
    today = datetime.datetime.now().strftime("%y%m%d")
    return f"{repo_name}#ST{today}"

def check_branch_for_prefix(repo, prefix: str, repo_name: str) -> Tuple[bool, Optional[str]]:
    """
    检查指定前缀是否已经有对应的分支
    
    :param repo: GitPython库的仓库对象
    :param prefix: 子树前缀路径
    :param repo_name: 仓库名称，用于生成分支名
    :return: (是否有对应分支, 分支名称或None)
    """
    # 根据仓库名和当前日期生成分支名
    split_branch_name = get_split_branch_name(repo_name)
    
    # 尝试查找前缀对应的分支
    try:
        # 检查本地是否已存在对应分支
        for branch in repo.branches:
            if branch.name == split_branch_name:
                return True, split_branch_name
            # 检查是否有以仓库名#ST开头的分支（即早期的split分支）
            elif branch.name.startswith(f"{repo_name}#ST"):
                return True, branch.name
                
        # 使用git命令查找是否有带subtree-split注释的提交
        # 这里我们执行一个git命令来查找subtree相关的提交
        cmd = ["log", "--grep=git-subtree-dir", f"--grep={prefix}", "--pretty=format:%H"]
        try:
            output = repo.git.execute(cmd)
            
            # 如果找到了相关提交，说明曾经进行过split
            if output.strip():
                return True, split_branch_name
        except Exception as e:
            console.print(f"[bold yellow]警告:[/] 执行git log查找时出错: {str(e)}")
            
        return False, split_branch_name
    except Exception as e:
        console.print(f"[bold red]检查分支时出错:[/] {str(e)}")
        return False, split_branch_name

def split_subtree(args=None, repo_info: Dict[str, Any] = None) -> bool:
    """
    为单个子树执行split操作，分离成独立分支 (使用 GitPython)
    
    :param args: 命令行参数
    :param repo_info: 仓库配置信息
    :return: 操作是否成功
    """
    repo = get_repo()
    if not repo:
        return False  # Error printed by get_repo

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
    prefix = repo_info.get("prefix", "")
    
    # 使用新命名规则生成分支名
    split_branch = get_split_branch_name(name)
    
    console.print(f"\n[bold cyan]正在为 {prefix} 执行 split 操作[/]")
    
    # 检查是否已经有对应分支
    has_branch, branch_name = check_branch_for_prefix(repo, prefix, name)
    
    # 即使有分支，我们也执行split以确保最新变更被分离出来
    # 构建 git subtree split 命令列表
    cmd_list = ["subtree", "split", f"--prefix={prefix}", f"--branch={split_branch}", "--rejoin"]
    
    # 显示完整命令
    cmd_str = " ".join(['git'] + cmd_list)
    console.print("\n[bold yellow]--- Git Split 命令 ---[/]")
    console.print(cmd_str)
    console.print("[bold yellow]------------------------[/]")

    # 执行命令
    success, output = run_git_command_stream(repo, cmd_list, show_command=False)

    if success:
        console.print(f"\n[bold green]成功为 {prefix} 执行 split 操作![/] 分支: {split_branch}")
        return True
    else:
        console.print(f"\n[bold red]为 {prefix} 执行 split 操作失败[/]")
        console.print("[yellow]提示:[/] 可能原因包括子树目录不存在或Git权限问题")
        return False

def split_all_subtrees(args=None) -> bool:
    """
    交互式为所有子树执行split操作 (使用 GitPython)
    
    :param args: 命令行参数
    :return: 操作是否成功
    """
    console.print("\n[bold cyan]--- Git Subtree Split 工具 ---[/]")
    
    # 检查是否在git仓库中
    if not validate_git_repo():
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    if check_working_tree():
        console.print("[bold yellow]警告:[/] 检测到工作区有未提交的更改。在执行split之前，请先提交这些更改。")
        console.print("[yellow]提示:[/] 使用 'git add .' 和 'git commit' 来提交更改")
        return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[bold yellow]警告:[/] 没有找到已配置的subtree仓库")
        return False
    
    # 显示将要执行split操作的仓库列表
    console.print("\n已配置的subtree仓库:")
    table = Table(show_header=True)
    table.add_column("#", style="dim")
    table.add_column("仓库名", style="cyan")
    table.add_column("Split分支", style="blue")
    table.add_column("本地路径", style="yellow")
    
    for i, repo in enumerate(repos):
        repo_name = repo.get("name", "")
        split_branch = get_split_branch_name(repo_name)
        table.add_row(
            str(i + 1),
            repo_name,
            split_branch,
            repo.get("prefix", "")
        )
    
    console.print(table)
    
    # 如果指定了仓库名，则只处理特定仓库
    selected_repos = repos
    if args and args.name:
        selected_repos = [repo for repo in repos if repo.get("name") == args.name]
        if not selected_repos:
            console.print(f"[bold red]错误:[/] 找不到名称为 '{args.name}' 的仓库")
            return False
    
    # 确认操作
    if not args or not getattr(args, "yes", False):
        if not Confirm.ask(f"\n是否为所有显示的 {len(selected_repos)} 个仓库执行split操作?"):
            console.print("[yellow]操作已取消[/]")
            return False
    
    # 执行split操作
    success_count = 0
    fail_count = 0
    
    for repo in selected_repos:
        if split_subtree(args, repo):
            success_count += 1
        else:
            fail_count += 1
    
    # 打印操作结果摘要
    console.print("\n[bold cyan]===操作结果摘要===[/]")
    console.print(f"• 总共尝试split: {len(selected_repos)} 个仓库")
    console.print(f"• 成功: {success_count} 个仓库")
    if fail_count > 0:
        console.print(f"• 失败: {fail_count} 个仓库")
    
    return fail_count == 0