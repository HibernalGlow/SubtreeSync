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

def select_multiple_from_list(title: str, items: List[T], display_func: Callable[[T], str] = str) -> List[T]:
    """
    从列表中选择多项
    
    Args:
        title: 选择标题
        items: 选项列表
        display_func: 用于将列表项转换为显示文本的函数
    
    Returns:
        选中的项列表，可能为空
    """
    if not items:
        console.print("[yellow]没有可选择的项目[/]")
        return []
    
    # 显示选项列表
    console.print(Panel(f"[bold green]{title}[/]"), style="green")
    
    # 创建美化后的菜单表格
    table = Table(show_header=True, box=None, border_style="dim")
    table.add_column("序号", style="cyan bold", justify="center", width=4)
    table.add_column("仓库名称", style="green bold")
    table.add_column("本地目录", style="blue")
    table.add_column("远程地址", style="magenta")
    
    for i, item in enumerate(items, 1):
        if isinstance(item, dict) and 'name' in item and 'prefix' in item:
            # 针对仓库对象进行丰富展示
            repo_name = f"[bold]{item['name']}[/]"
            prefix = f"[blue]{item['prefix']}[/]"
            remote = item.get('remote', '未知')
            remote_display = f"[dim]{remote.split('/')[-1]}[/]" if remote != '未知' else "[red]未知[/]"
            table.add_row(f"{i}", repo_name, prefix, remote_display)
        else:
            # 如果不是仓库对象，使用传入的格式化函数
            table.add_row(f"{i}", display_func(item), "", "")
    
    console.print(table)
    console.print("[bold cyan]提示:[/] 输入多个数字用空格分隔(例如: 1 3 5)，输入[bold]0[/]选择全部，直接回车取消")
    
    # 获取用户输入
    while True:
        choice = Prompt.ask("请输入选项对应的序号").strip().lower()
        
        # 空输入表示取消
        if not choice:
            return []
        
        # '0' 表示全选
        if choice == '0':
            return items.copy()
        
        # 否则解析数字
        try:
            selected_indices = []
            for num in choice.split():
                idx = int(num) - 1
                if 0 <= idx < len(items):
                    selected_indices.append(idx)
                else:
                    raise ValueError(f"数字 {num} 超出范围")
            
            # 排序并去重
            selected_indices = sorted(set(selected_indices))
            return [items[i] for i in selected_indices]
        except ValueError as e:
            console.print(f"[bold red]错误:[/] 请输入有效的数字 (1-{len(items)}) 或 '0'全选")

def select_repos_for_action(repos: List[Dict[str, Any]], action: str) -> List[Dict[str, Any]]:
    """
    为操作选择多个仓库
    
    Args:
        repos: 仓库列表
        action: 操作名称，用于显示
    
    Returns:
        选中的仓库列表
    """
    # 仓库对象已经在select_multiple_from_list中特殊处理，不需要format_repo函数
    return select_multiple_from_list(f"请选择要{action}的仓库", repos, lambda r: r['name'])
