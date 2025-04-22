#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用工具函数模块
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.prompt import IntPrompt, Prompt
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

# 创建Rich控制台对象
console = Console()

def get_config_dir() -> Path:
    """获取配置文件目录"""
    # 获取脚本所在的目录
    script_dir = Path(__file__).resolve().parent.parent
    return script_dir

def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_config_dir() / "subtree_repos.json"

def ensure_config_exists():
    """确保配置文件存在"""
    config_path = get_config_path()
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"repos": []}, f, ensure_ascii=False, indent=2)

def load_subtree_repos() -> List[Dict[str, Any]]:
    """加载已保存的subtree仓库配置"""
    ensure_config_exists()
    try:
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("repos", [])
    except Exception as e:
        console.print(f"[bold red]读取配置文件失败:[/] {str(e)}")
        return []

def save_subtree_repo(repo_info: Dict[str, str]) -> bool:
    """保存subtree仓库配置"""
    repos = load_subtree_repos()
    
    # 检查是否已存在
    for i, repo in enumerate(repos):
        if repo.get("name") == repo_info["name"]:
            # 更新已存在的配置
            repos[i] = repo_info
            break
    else:
        # 添加新配置
        repos.append(repo_info)
    
    try:
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump({"repos": repos}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        console.print(f"[bold red]保存配置文件失败:[/] {str(e)}")
        return False

def run_command(cmd: List[str], show_command: bool = True) -> Tuple[bool, str]:
    """
    执行命令并返回结果
    :param cmd: 命令列表
    :param show_command: 是否显示执行的命令
    :return: (成功标志, 输出结果)
    """
    if show_command:
        cmd_str = " ".join(cmd)
        console.print(f"[dim]$ {cmd_str}[/]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]执行命令中..."),
            transient=True,
        ) as progress:
            progress.add_task("", total=None)
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def validate_git_repo() -> bool:
    """检查当前是否在git仓库中"""
    success, output = run_command(["git", "rev-parse", "--is-inside-work-tree"], show_command=False)
    return success and output.strip() == "true"

def check_working_tree() -> bool:
    """检查工作区状态，返回是否有未提交的更改"""
    success, output = run_command(["git", "status", "--porcelain"], show_command=False)
    return bool(output.strip())

def extract_repo_name(url: str) -> str:
    """从仓库URL中提取项目名"""
    # 处理以下格式:
    # https://github.com/username/repo.git
    # git@github.com:username/repo.git
    url = url.strip()
    if url.endswith('.git'):
        url = url[:-4]
    
    if ":" in url:  # SSH格式
        parts = url.split(":")[-1].split("/")
    else:  # HTTP(S)格式
        parts = url.split("/")
    
    if parts:
        return parts[-1]
    
    return ""

def list_git_remotes() -> List[Dict[str, str]]:
    """获取当前git仓库的所有远程仓库"""
    try:
        result = subprocess.run(
            ["git", "remote"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        remotes = []
        for remote in result.stdout.strip().split("\n"):
            if remote:
                url_result = subprocess.run(
                    ["git", "remote", "get-url", remote],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                remotes.append({
                    "name": remote,
                    "url": url_result.stdout.strip()
                })
        return remotes
    except Exception:
        return []

def show_numeric_menu(options: List[str], title: str = "请选择一个选项:", default: int = None) -> int:
    """