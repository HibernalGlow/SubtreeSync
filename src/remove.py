#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 删除功能
实现删除已添加的 git subtree 的功能
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional, Any, List

try:
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

from .console import console
from .interactive import confirm_action
from .utils import (
    validate_git_repo, check_working_tree,
    load_subtree_repos, delete_subtree_repo, find_repo_by_name,
    get_repo, run_git_command_stream, run_command
)

def remove_subtree(args=None) -> bool:
    """
    删除一个git subtree
    
    Args:
        args: 命令行参数
        
    Returns:
        是否成功删除
    """
    console.print("\n[bold cyan]--- Git Subtree 删除工具 ---[/]")

    # 检查是否在git仓库中
    if not validate_git_repo():
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    if check_working_tree():
        console.print("[bold yellow]警告:[/] 检测到工作区有未提交的修改。在删除子树前，建议先提交或暂存这些更改。")
        if not confirm_action("是否继续操作?"):
            console.print("[yellow]操作已取消[/]")
            return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[bold yellow]警告:[/] 没有找到已配置的子树仓库")
        console.print("[cyan]提示:[/] 请先使用 'subtree-sync add' 命令添加子树仓库")
        return False
    
    # 如果传入了参数中指定了仓库名称，直接使用
    repo_name = None
    if args and getattr(args, "name", None):
        repo_name = args.name
    
    selected_repo = None
    
    # 如果指定了名称，查找对应的仓库
    if repo_name:
        selected_repo = find_repo_by_name(repo_name)
        if not selected_repo:
            console.print(f"[bold red]错误:[/] 找不到名称为 '{repo_name}' 的子树仓库")
            return False
    else:
        # 显示所有仓库信息供用户选择
        console.print("\n已配置的子树仓库:")
        table = Table(show_header=True)
        table.add_column("#", style="dim")
        table.add_column("仓库名", style="cyan")
        table.add_column("本地路径", style="yellow")
        table.add_column("远程地址", style="green")
        
        for i, repo in enumerate(repos):
            table.add_row(
                str(i + 1),
                repo.get("name", ""),
                repo.get("prefix", ""),
                repo.get("remote", "")
            )
        
        console.print(table)
        
        # 让用户选择要删除的仓库
        choice = None
        while True:
            choice = Prompt.ask(
                "[bold cyan]请输入要删除的仓库序号[/] (输入q取消)",
                default="q"
            )
            
            if choice.lower() == 'q':
                console.print("[yellow]操作已取消[/]")
                return False
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(repos):
                    selected_repo = repos[idx]
                    break
                else:
                    console.print("[bold red]错误:[/] 无效的序号，请重新输入")
            except ValueError:
                console.print("[bold red]错误:[/] 请输入有效的数字或q退出")
    
    # 显示将要删除的仓库信息
    name = selected_repo.get("name", "")
    prefix = selected_repo.get("prefix", "")
    remote = selected_repo.get("remote", "")
    branch = selected_repo.get("branch", "main")
    
    console.print(f"\n[bold]将要删除以下子树:[/]", style="yellow")
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("键", style="bold cyan")
    table.add_column("值")
    
    table.add_row("仓库名", name)
    table.add_row("本地路径", prefix)
    table.add_row("远程地址", remote)
    table.add_row("分支", branch)
    
    console.print(table)
    
        console.print(table)
        
        # 让用户选择要删除的仓库
        choice = None
        while True:
            choice = Prompt.ask(
                "[bold cyan]请输入要删除的仓库序号[/] (输入q取消)",
                default="q"
            )
            
            if choice.lower() == 'q':
                console.print("[yellow]操作已取消[/]")
                return False
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(repos):
                    selected_repo = repos[idx]
                    break
                else:
                    console.print("[bold red]错误:[/] 无效的序号，请重新输入")
            except ValueError:
                console.print("[bold red]错误:[/] 请输入有效的数字或q退出")
    
    # 显示将要删除的仓库信息
    name = selected_repo.get("name", "")
    prefix = selected_repo.get("prefix", "")
    remote = selected_repo.get("remote", "")
    branch = selected_repo.get("branch", "main")
    
    console.print(f"\n[bold]将要删除以下子树:[/]", style="yellow")
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("键", style="bold cyan")
    table.add_column("值")
    
    table.add_row("仓库名", name)
    table.add_row("本地路径", prefix)
    table.add_row("远程地址", remote)
    table.add_row("分支", branch)
    
    console.print(table)
    
    # 确认用户想要删除的内容
    delete_config_only = False
    delete_files = False
    delete_taskfile = False
    
    console.print("\n[bold cyan]请选择删除操作:[/]")
    delete_config_only = Confirm.ask("仅从配置文件中移除？(不删除实际文件)", default=False)
    
    if not delete_config_only:
        delete_files = Confirm.ask("同时删除本地文件？", default=True)
    
    delete_taskfile = Confirm.ask("从Taskfile.yml中移除配置？", default=True)
    
    # 最终确认
    console.print("\n[bold red]警告：此操作不可逆！[/]")
    if not confirm_action("确定要执行删除操作吗?"):
        console.print("[yellow]操作已取消[/]")
        return False
    
    success = True
    
    # 1. 从配置文件中删除
    if delete_subtree_repo(name):
        console.print(f"[green]已从配置文件中删除仓库 '{name}'[/]")
    else:
        console.print(f"[bold red]从配置文件删除仓库 '{name}' 失败[/]")
        success = False
    
    # 2. 从Taskfile.yml中移除
    if delete_taskfile:
        if remove_from_taskfile(prefix):
            console.print(f"[green]已从Taskfile.yml中移除子树配置[/]")
        else:
            console.print(f"[bold yellow]从Taskfile.yml移除配置失败，可能需要手动移除[/]")
            success = False
    
    # 3. 删除本地文件
    if delete_files:
        prefix_path = Path(prefix)
        if prefix_path.exists():
            try:
                import shutil
                # 先确认路径存在且不是根目录，避免误删除
                if str(prefix_path) != "." and str(prefix_path) != "/" and prefix_path.exists():
                    console.print(f"[yellow]正在删除目录: {prefix}[/]")
                    
                    # 删除目录
                    shutil.rmtree(prefix_path)
                    console.print(f"[green]已删除本地目录: {prefix}[/]")
                    
                    # 提示用户可能需要提交此更改
                    console.print(f"[cyan]提示: 你可能需要提交此更改: git add -A && git commit -m '删除子树 {name}'[/]")
                else:
                    console.print(f"[bold red]安全检查失败！路径 '{prefix}' 不安全，无法删除。[/]")
                    success = False
            except Exception as e:
                console.print(f"[bold red]删除本地文件时出错:[/] {str(e)}")
                success = False
        else:
            console.print(f"[bold yellow]警告:[/] 本地路径 '{prefix}' 不存在")
    
    if success:
        console.print(f"\n[bold green]已成功删除子树 '{name}'[/]")
    else:
        console.print(f"\n[bold yellow]删除子树 '{name}' 过程中出现一些问题，请检查上述输出[/]")
    
    return success

def remove_all_subtrees(args=None) -> bool:
    """
    批量删除多个子树(谨慎使用)
    
    Args:
        args: 命令行参数
        
    Returns:
        是否成功删除
    """
    console.print("\n[bold cyan]--- Git Subtree 批量删除工具 ---[/]")
    console.print("[bold red]警告：此功能将批量删除多个子树，操作不可逆！[/]")
    
    # 此功能需要显式通过命令行参数启用，不在交互式模式中提供
    if not args or not getattr(args, "batch", False):
        console.print("[bold red]错误:[/] 必须指定--batch参数以启用批量删除功能")
        console.print("[yellow]提示:[/] 此功能非常危险，仅在确实需要时使用")
        return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[bold yellow]警告:[/] 没有找到已配置的子树仓库")
        return False
    
    # 显示所有仓库信息
    console.print("\n已配置的子树仓库:")
    table = Table(show_header=True)
    table.add_column("#", style="dim")
    table.add_column("仓库名", style="cyan")
    table.add_column("本地路径", style="yellow")
    
    for i, repo in enumerate(repos):
        table.add_row(
            str(i + 1),
            repo.get("name", ""),
            repo.get("prefix", "")
        )
    
    console.print(table)
    
    # 严格确认
    console.print("\n[bold red]警告：你即将批量删除所有列出的子树！[/]")
    console.print("[bold red]此操作极其危险且不可逆！[/]")
    
    if not Confirm.ask(
        "[bold red]你确定要继续操作吗？请再三确认！[/]",
        default=False
    ):
        console.print("[yellow]操作已取消[/]")
        return False
    
    # 最终确认
    verify_text = "DELETE ALL SUBTREES"
    input_text = Prompt.ask(
        f"[bold red]请输入 '{verify_text}' 以确认删除所有子树[/]"
    )
    
    if input_text != verify_text:
        console.print("[yellow]输入不匹配，操作已取消[/]")
        return False
    
    # 执行删除操作
    success_count = 0
    fail_count = 0
    
    # 询问是否删除文件
    delete_files = Confirm.ask("是否同时删除本地文件?", default=False)
    delete_taskfile = Confirm.ask("是否从Taskfile.yml中移除所有配置?", default=False)
    
    for repo in repos:
        name = repo.get("name", "")
        prefix = repo.get("prefix", "")
        
        console.print(f"\n[bold cyan]正在删除子树:[/] {name} ({prefix})")
        
        # 1. 从配置文件中删除
        config_deleted = delete_subtree_repo(name)
        if config_deleted:
            console.print(f"[green]已从配置文件中删除仓库 '{name}'[/]")
        else:
            console.print(f"[bold red]从配置文件删除仓库 '{name}' 失败[/]")
        
        # 2. 从Taskfile.yml中移除
        if delete_taskfile:
            if remove_from_taskfile(prefix):
                console.print(f"[green]已从Taskfile.yml中移除子树配置[/]")
            else:
                console.print(f"[bold yellow]从Taskfile.yml移除配置失败，可能需要手动移除[/]")
        
        # 3. 删除本地文件
        if delete_files:
            prefix_path = Path(prefix)
            if prefix_path.exists():
                try:
                    import shutil
                    # 先确认路径存在且不是根目录，避免误删除
                    if str(prefix_path) != "." and str(prefix_path) != "/" and prefix_path.exists():
                        console.print(f"[yellow]正在删除目录: {prefix}[/]")
                        
                        # 删除目录
                        shutil.rmtree(prefix_path)
                        console.print(f"[green]已删除本地目录: {prefix}[/]")
                    else:
                        console.print(f"[bold red]安全检查失败！路径 '{prefix}' 不安全，无法删除。[/]")
                except Exception as e:
                    console.print(f"[bold red]删除本地文件时出错:[/] {str(e)}")
                    fail_count += 1
                    continue
            else:
                console.print(f"[bold yellow]警告:[/] 本地路径 '{prefix}' 不存在")
        
        success_count += 1
    
    # 提示用户可能需要提交此更改
    if delete_files:
        console.print(f"\n[cyan]提示: 你可能需要提交此更改: git add -A && git commit -m '删除所有子树'[/]")
    
    # 打印操作结果摘要
    console.print("\n[bold cyan]===操作结果摘要===[/]")
    console.print(f"• 总共尝试删除: {len(repos)} 个仓库")
    console.print(f"• 成功删除: {success_count} 个仓库")
    if fail_count > 0:
        console.print(f"• 失败: {fail_count} 个仓库")
    
    return fail_count == 0