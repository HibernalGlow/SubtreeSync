#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 拉取更新功能
实现从远程仓库拉取子树更新
"""

import sys
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import git # Import GitPython

try:
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.progress import Progress
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

from .interactive import confirm_action
from .utils import (
    validate_git_repo, check_working_tree,
    load_subtree_repos,
    get_repo, run_command_direct # 替换为 run_command_direct
)

def pull_subtree(args=None, repo_info: Dict[str, Any] = None) -> bool:
    """
    拉取单个子树的更新 (使用 GitPython)
    :param args: 命令行参数
    :param repo_info: 仓库配置信息
    :return: 操作是否成功
    """
    repo = get_repo()
    if not repo:
        return False # Error printed by get_repo

    # 确保repo_info是有效的
    if not repo_info:
        if not args or not getattr(args, "name", None):
            print("错误: 没有指定仓库信息或名称")
            return False
            
        # 尝试通过名称查找仓库信息
        from .utils import find_repo_by_name
        repo_name = args.name
        repo_info = find_repo_by_name(repo_name)
        if not repo_info:
            print(f"错误: 找不到名称为 '{repo_name}' 的仓库")
            return False
    
    name = repo_info.get("name", "")
    remote = repo_info.get("remote", "")
    prefix = repo_info.get("prefix", "")
    branch = repo_info.get("branch", "main")
    
    print(f"\n从 {name} 拉取更新到 {prefix}")

    # 构建 git subtree pull 命令列表
    cmd_list = ["git", "subtree", "pull", f"--prefix={prefix}", name, branch, "--squash"]

    # 显示完整命令
    cmd_str = " ".join(cmd_list)
    print("\n--- Git Pull 命令 ---")
    print(cmd_str)
    print("---------------------")

    # 执行命令，使用直接执行方法
    success = run_command_direct(cmd_list)

    if success:
        print(f"\n从 {name} 成功拉取更新!")
        return True
    else:
        print(f"\n从 {name} 拉取更新失败")
        print("提示: 如果出现冲突，请手动解决后再继续")
        return False

def pull_all_subtrees(args=None) -> bool:
    """
    交互式拉取所有子树更新 (使用 GitPython)
    :param args: 命令行参数
    :return: 操作是否成功
    """
    print("\n--- Git Subtree 拉取更新工具 ---")
    
    # 检查是否在git仓库中
    if not validate_git_repo(): # Uses GitPython now
        print("错误: 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    if check_working_tree(): # Uses GitPython now
        print("警告: 检测到工作区有未提交的更改。建议先提交或暂存这些更改。")
        if not confirm_action("是否继续操作?"):
            print("操作已取消")
            return False
    
    # 加载所有仓库配置
    repos = load_subtree_repos()
    
    if not repos:
        print("警告: 没有找到已配置的subtree仓库")
        return False
    
    # 显示将要拉取更新的仓库列表
    print("\n已配置的subtree仓库:")
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
    
    print(table)
    
    # 如果指定了仓库名，则只拉取特定仓库
    selected_repos = repos
    if args and args.name:
        selected_repos = [repo for repo in repos if repo.get("name") == args.name]
        if not selected_repos:
            print(f"错误: 找不到名称为 '{args.name}' 的仓库")
            return False
    
    # 确认操作
    if not args or not args.yes:
        if not confirm_action(f"\n是否拉取所有显示的 {len(selected_repos)} 个仓库的更新?"):
            print("操作已取消")
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
    print("\n===操作结果摘要===")
    print(f"• 总共尝试拉取: {len(selected_repos)} 个仓库")
    print(f"• 成功拉取: {success_count} 个仓库")
    if fail_count > 0:
        print(f"• 失败: {fail_count} 个仓库")
    
    return fail_count == 0