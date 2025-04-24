#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree Split功能
实现将本地子树目录分离为独立分支，为推送做准备
"""

import sys
import os
import subprocess
import datetime
import tempfile
from typing import Dict, List, Optional, Any, Union, Tuple

try:
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

try:
    import pyperclip  # 用于复制内容到剪贴板
except ImportError:
    pyperclip = None

from .console import console  # 导入共享的控制台实例
from .interactive import confirm_action
from .utils import (
    validate_git_repo, check_working_tree,
    load_subtree_repos, find_repo_by_name,
    run_git_command_stream, run_command
)

def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到剪贴板
    
    :param text: 要复制的文本
    :return: 是否成功复制
    """
    if pyperclip is None:
        console.print("[bold yellow]警告:[/] 未安装pyperclip库，无法使用剪贴板功能")
        console.print("[dim]可以通过运行 'pip install pyperclip' 安装[/]")
        return False
    
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        console.print(f"[bold red]复制到剪贴板时出错:[/] {str(e)}")
        return False

def get_split_branch_name(repo_name: str) -> str:
    """
    根据仓库名生成split分支名，格式为"仓库名#ST日期"
    
    :param repo_name: 仓库名称
    :return: 生成的分支名
    """
    today = datetime.datetime.now().strftime("%y%m%d")
    return f"{repo_name}#ST{today}"

def run_git_command(cmd_args: List[str], show_output: bool = False) -> Tuple[bool, str]:
    """
    使用子进程执行Git命令
    
    :param cmd_args: Git命令参数列表
    :param show_output: 是否显示输出
    :return: (成功与否, 输出内容)
    """
    full_cmd = ["git"] + cmd_args
    
    if not show_output:
        # 对于不需要显示输出的命令，使用简单的subprocess.run
        try:
            process = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return process.returncode == 0, process.stdout + (f"\n{process.stderr}" if process.stderr else "")
        except Exception as e:
            return False, str(e)
    
    # 对于需要显示输出的命令，使用实时输出的方式
    return run_command(full_cmd)

def check_branch_for_prefix(repo_dir: str, prefix: str, repo_name: str) -> Tuple[bool, Optional[str]]:
    """
    检查指定前缀是否已经有对应的分支
    
    :param repo_dir: Git仓库目录
    :param prefix: 子树前缀路径
    :param repo_name: 仓库名称，用于生成分支名
    :return: (是否有对应分支, 分支名称或None)
    """
    # 根据仓库名和当前日期生成分支名
    split_branch_name = get_split_branch_name(repo_name)
    
    # 尝试查找前缀对应的分支
    try:
        # 检查本地是否已存在对应分支
        success, output = run_git_command(["branch"], False)
        if success:
            branches = [b.strip() for b in output.split('\n') if b.strip()]
            for branch in branches:
                # 移除分支名称前的'*'和空格
                clean_name = branch.replace('*', '').strip()
                if clean_name == split_branch_name:
                    return True, split_branch_name
                # 检查是否有以仓库名#ST开头的分支（即早期的split分支）
                elif clean_name.startswith(f"{repo_name}#ST"):
                    return True, clean_name
        
        # 使用git命令查找是否有带subtree-split注释的提交
        cmd = ["log", "--grep=git-subtree-dir", f"--grep={prefix}", "--pretty=format:%H"]
        success, output = run_git_command(cmd, False)
        
        # 如果找到了相关提交，说明曾经进行过split
        if success and output.strip():
            return True, split_branch_name
        
        return False, split_branch_name
    except Exception as e:
        console.print(f"[bold red]检查分支时出错:[/] {str(e)}")
        return False, split_branch_name

def run_command_or_copy(cmd: List[str], cmd_str: str, copy_only: bool = False) -> Tuple[bool, str]:
    """
    执行命令或复制命令到剪贴板
    
    :param cmd: 命令参数列表
    :param cmd_str: 命令完整字符串，用于复制
    :param copy_only: 是否只复制不执行
    :return: (是否成功, 输出信息)
    """
    if copy_only:
        if copy_to_clipboard(cmd_str):
            console.print("[bold green]命令已复制到剪贴板！[/] 您可以自行粘贴并执行")
            return True, "命令已复制到剪贴板"
        else:
            console.print("[bold red]复制命令到剪贴板失败[/]")
            if not Confirm.ask("是否继续执行命令?"):
                return False, "操作已取消"
    
    # 执行命令 - 使用新的直接执行方法
    from .utils import run_git_command_direct
    success = run_git_command_direct(cmd, True)
    return success, "" # 不再返回输出内容

def split_subtree(args=None, repo_info: Dict[str, Any] = None) -> bool:
    """
    为单个子树执行split操作，分离成独立分支
    
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
    prefix = repo_info.get("prefix", "")
    
    # 使用新命名规则生成分支名
    split_branch = get_split_branch_name(name)
    
    console.print(f"\n[bold cyan]正在为 {prefix} 执行 split 操作[/]")
    
    # 检查是否已经有对应分支
    has_branch, branch_name = check_branch_for_prefix(".", prefix, name)
    
    # 即使有分支，我们也执行split以确保最新变更被分离出来
    # 构建 git subtree split 命令列表
    cmd_list = ["subtree", "split", f"--prefix={prefix}", f"--branch={split_branch}", "--rejoin"]
    
    # 显示完整命令
    cmd_str = " ".join(['git'] + cmd_list)
    console.print("\n[bold yellow]--- Git Split 命令 ---[/]")
    console.print(cmd_str)
    console.print("[bold yellow]------------------------[/]")

    # 检查是否只复制命令而不执行
    copy_only = getattr(args, "copy_only", False) if args else False
    success, output = run_command_or_copy(cmd_list, cmd_str, copy_only)

    if success:
        console.print(f"\n[bold green]成功为 {prefix} 执行 split 操作![/] 分支: {split_branch}")
        return True
    else:
        console.print(f"\n[bold red]为 {prefix} 执行 split 操作失败[/]")
        console.print("[yellow]提示:[/] 可能原因包括子树目录不存在或Git权限问题")
        if output:
            print("\n错误信息:")
            print(output)
        return False

def split_all_subtrees(args=None) -> bool:
    """
    交互式为所有子树执行split操作
    
    :param args: 命令行参数
    :return: 操作是否成功
    """
    console.print("\n[bold cyan]--- Git Subtree Split 工具 ---[/]")
    
    # 检查是否在git仓库中
    success, _ = run_git_command(["rev-parse", "--is-inside-work-tree"], False)
    if not success:
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    success, output = run_git_command(["status", "--porcelain"], False)
    if success and output.strip():
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
    
    # 检查是否只复制命令
    copy_only = getattr(args, "copy_only", False) if args else False
    if copy_only and not pyperclip:
        console.print("[bold yellow]警告:[/] 复制到剪贴板功能需要pyperclip库，但未安装")
        console.print("[yellow]提示:[/] 可以通过运行 'pip install pyperclip' 安装")
        if Confirm.ask("是否继续并直接执行命令?"):
            copy_only = False
        else:
            console.print("[yellow]操作已取消[/]")
            return False
    
    # 执行split操作
    success_count = 0
    fail_count = 0
    
    for repo in selected_repos:
        # 如果是批量模式且需要复制到剪贴板，我们只复制第一个命令
        if copy_only and len(selected_repos) > 1:
            if success_count == 0:
                console.print("[bold yellow]由于选择了多个仓库且启用了复制模式，只有第一个命令会被复制到剪贴板[/]")
        
        # 传递copy_only参数到split_subtree函数
        if copy_only:
            # 创建临时参数对象，带有copy_only和name属性
            class TempArgs:
                pass
            temp_args = TempArgs()
            temp_args.copy_only = True
            temp_args.name = repo.get("name", "")
            temp_args.yes = True
            
            if split_subtree(temp_args, repo):
                success_count += 1
            else:
                fail_count += 1
            
            # 复制后只处理第一个仓库
            if len(selected_repos) > 1:
                console.print("[bold yellow]由于您选择了复制模式，其余仓库命令需要手动生成[/]")
                break
        else:
            # 正常执行
            if split_subtree(args, repo):
                success_count += 1
            else:
                fail_count += 1
    
    # 打印操作结果摘要
    console.print("\n[bold cyan]===操作结果摘要===[/]")
    if copy_only:
        console.print(f"• 总共生成命令: {success_count} 个仓库")
        console.print(f"• 成功复制到剪贴板: {success_count} 个命令")
    else:
        console.print(f"• 总共尝试split: {len(selected_repos)} 个仓库")
        console.print(f"• 成功: {success_count} 个仓库")
    
    if fail_count > 0:
        console.print(f"• 失败: {fail_count} 个仓库")
    
    return fail_count == 0