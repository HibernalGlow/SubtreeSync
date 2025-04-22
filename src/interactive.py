#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式菜单模块，提供数字选择功能
"""

from typing import List, Dict, Any, Optional, Callable, TypeVar, Union
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

T = TypeVar('T')

console = Console()

def show_menu(title: str, options: List[str]) -> int:
    """
    显示菜单并返回用户选择的索引
    
    Args:
        title: 菜单标题
        options: 选项列表
    
    Returns:
        用户选择的索引，从0开始
    """
    console.print(Panel(f"[bold green]{title}[/]"), style="green")
    
    # 创建菜单表格
    table = Table(show_header=False, box=None)
    table.add_column("序号", style="cyan", justify="right")
    table.add_column("选项", style="green")
    
    for i, option in enumerate(options, 1):
        table.add_row(f"{i}", option)
    
    console.print(table)
    
    # 获取用户输入
    while True:
        choice = Prompt.ask("请输入选项对应的序号", console=console)
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                return choice_idx
            else:
                console.print(f"[bold red]错误:[/] 请输入1-{len(options)}之间的数字")
        except ValueError:
            console.print("[bold red]错误:[/] 请输入有效的数字")

def select_from_list(title: str, items: List[T], display_func: Callable[[T], str] = str,
                     allow_cancel: bool = True) -> Optional[T]:
    """
    从列表中选择一项
    
    Args:
        title: 选择标题
        items: 选项列表
        display_func: 用于将列表项转换为显示文本的函数
        allow_cancel: 是否允许取消选择
    
    Returns:
        选中的项，若取消则返回None
    """
    if not items:
        console.print("[yellow]没有可选择的项目[/]")
        return None
    
    options = [display_func(item) for item in items]
    if allow_cancel:
        options.append("取消")
    
    choice_idx = show_menu(title, options)
    
    if allow_cancel and choice_idx == len(items):
        return None
    
    return items[choice_idx]

def select_mode() -> Optional[str]:
    """
    选择操作模式
    
    Returns:
        选择的模式，取消则返回None
    """
    modes = ["添加子树", "拉取更新", "推送更新", "列出子树"]
    mode_cmds = ["add", "pull", "push", "list"]
    
    choice_idx = show_menu("请选择操作模式", modes + ["退出"])
    
    if choice_idx == len(modes):
        return None
    
    return mode_cmds[choice_idx]

def select_repo(repos: List[Dict[str, Any]], action: str) -> Optional[Dict[str, Any]]:
    """
    选择一个仓库
    
    Args:
        repos: 仓库列表
        action: 操作名称，用于显示
    
    Returns:
        选中的仓库信息，取消则返回None
    """
    def format_repo(repo: Dict[str, Any]) -> str:
        return f"{repo['name']} ({repo['prefix']}) - {repo.get('remote', '未知远程地址')}"
    
    return select_from_list(f"请选择要{action}的仓库", repos, format_repo)

def confirm_action(message: str) -> bool:
    """
    确认操作
    
    Args:
        message: 确认消息
    
    Returns:
        True表示确认，False表示取消
    """
    return Confirm.ask(message, console=console)

def show_operation_result(success: bool, operation: str, details: str = ""):
    """
    显示操作结果
    
    Args:
        success: 操作是否成功
        operation: 操作名称
        details: 详细信息
    """
    if success:
        console.print(f"[bold green]{operation}成功[/]")
        if details:
            console.print(details)
    else:
        console.print(f"[bold red]{operation}失败[/]")
        if details:
            console.print(f"[red]{details}[/]")
