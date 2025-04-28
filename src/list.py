#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 列表功能
显示所有已配置的subtree仓库信息
"""

import sys
from typing import Dict, List, Optional, Any, Union

try:
    from rich.panel import Panel
    from rich.table import Table
    from rich.console import Console
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

from .utils import (
    console, load_subtree_repos, get_current_repository, get_default_repository, load_all_repositories
)

def list_subtrees(args=None) -> bool:
    """
    列出所有已配置的subtree仓库
    :param args: 命令行参数
    :return: 操作是否成功
    """
    # 获取当前仓库信息
    current_repo = get_current_repository()
    
    if not current_repo:
        console.print("[bold yellow]警告:[/] 未找到有效的仓库配置")
        console.print("[cyan]提示:[/] 请先添加仓库配置")
        return True
    
    # 显示仓库标题
    repo_name = current_repo.get("name", "未命名仓库")
    repo_path = current_repo.get("path", "未知路径")
    
    console.print(Panel.fit(
        f"[bold green]Git Subtree 仓库列表 - {repo_name}[/]\n[dim]{repo_path}[/]", 
        border_style="green", 
        title=f"SubtreeSync",
        subtitle="v1.0")
    )
    
    # 加载当前仓库的子树配置
    repos = load_subtree_repos()
    
    if not repos:
        console.print(f"[bold yellow]仓库 {repo_name} 中没有找到已配置的subtree项目[/]")
        console.print("[cyan]提示:[/] 请先使用 'subtree-sync add' 命令添加subtree仓库")
        return True
    
    # 显示所有仓库信息
    console.print(f"\n[bold]已配置的subtree项目 ({len(repos)}个):[/]")
    
    table = Table(show_header=True)
    table.add_column("#", style="dim")
    table.add_column("仓库名", style="cyan")
    table.add_column("远程地址", style="green")
    table.add_column("分支", style="blue")
    table.add_column("本地路径", style="yellow")
    table.add_column("添加时间", style="magenta")
    
    for i, repo in enumerate(repos):
        added_time = repo.get("added_time", "未知")
        # 只保留日期部分，去掉时间
        if "T" in added_time:
            added_time = added_time.split("T")[0]
            
        table.add_row(
            str(i + 1),
            repo.get("name", ""),
            repo.get("remote", ""),
            repo.get("branch", "main"),
            repo.get("prefix", ""),
            added_time
        )
    
    console.print(table)
    
    # 如果有参数且要求详细信息，则显示更多信息
    if args and args.verbose:
        console.print("\n[bold]详细信息:[/]")
        for i, repo in enumerate(repos):
            console.print(f"\n[bold cyan]仓库 {i+1}: {repo.get('name', '')}[/]")
            panel_content = []
            for key, value in repo.items():
                if key != "extra":  # 忽略扩展字段
                    panel_content.append(f"[bold]{key}[/]: {value}")
            
            # 显示额外信息
            if "extra" in repo and repo["extra"]:
                panel_content.append("\n[bold]额外信息:[/]")
                for extra_key, extra_value in repo["extra"].items():
                    panel_content.append(f"[bold]{extra_key}[/]: {extra_value}")
            
            console.print(Panel("\n".join(panel_content), 
                              title=f"仓库详情 - {repo.get('name', '')}", 
                              border_style="blue"))
    
    # 显示所有可用仓库的列表
    if args and args.verbose:
        console.print("\n[bold]所有可用仓库:[/]")
        available_repos = load_all_repositories()
        repo_table = Table(show_header=True)
        repo_table.add_column("仓库名", style="cyan")
        repo_table.add_column("路径", style="green")
        repo_table.add_column("状态", style="yellow")
        
        for repo in available_repos:
            name = repo.get("name", "无名称")
            path = repo.get("path", ".")
            status = []
            
            if repo.get("name") == current_repo.get("name"):
                status.append("[green]当前[/]")
            if repo.get("is_default", False):
                status.append("[cyan]默认[/]")
                
            status_str = ", ".join(status) if status else ""
            
            repo_table.add_row(name, path, status_str)
        
        console.print(repo_table)
    
    return True