#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用工具函数模块
"""

import os
import sys
import json
import subprocess
import io # Import io module
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
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

def find_repo_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    根据名称查找仓库配置
    
    Args:
        name: 仓库名称
        
    Returns:
        找到的仓库配置，未找到则返回None
    """
    repos = load_subtree_repos()
    for repo in repos:
        if repo.get("name") == name:
            return repo
    return None

def delete_subtree_repo(name: str) -> bool:
    """
    删除subtree仓库配置
    
    Args:
        name: 仓库名称
        
    Returns:
        是否成功删除
    """
    repos = load_subtree_repos()
    initial_count = len(repos)
    
    # 过滤掉要删除的仓库
    repos = [repo for repo in repos if repo.get("name") != name]
    
    if len(repos) == initial_count:
        # 没有找到要删除的仓库
        return False
    
    try:
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump({"repos": repos}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        console.print(f"[bold red]保存配置文件失败:[/] {str(e)}")
        return False

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
    执行命令并返回结果，使用subprocess.run并强制UTF-8解码（替换错误）。
    :param cmd: 命令列表
    :param show_command: 是否显示执行的命令
    :return: (成功标志, 完整输出结果)
    """
    if show_command:
        cmd_str = " ".join(cmd)
        console.print(f"[dim]$ {cmd_str}[/]")

    try:
        # 使用 subprocess.run，捕获字节输出
        # 移除环境变量设置，保持简单
        result = subprocess.run(
            cmd,
            capture_output=True, # Capture stdout and stderr as bytes
            check=False          # Don't raise exception on non-zero exit
        )

        # --- 解码 ---
        # 始终使用 UTF-8 解码，替换无法解码的字节。这是最简单且兼容性较好的方法。
        stdout_str = result.stdout.decode('utf-8', errors='replace')
        stderr_str = result.stderr.decode('utf-8', errors='replace')

        # --- 打印 ---
        # 直接打印解码后的字符串，让 rich 处理换行和格式
        # 使用 strip() 移除首尾可能多余的空白或换行符
        if stdout_str:
            console.print(stdout_str.strip())
        if stderr_str:
            console.print(f"[red]{stderr_str.strip()}[/]")

        # --- 返回 ---
        # 合并输出用于返回
        output = stdout_str + stderr_str

        # 根据返回码判断成功与否
        return result.returncode == 0, output.strip()

    except FileNotFoundError:
        error_msg = f"错误: 命令或程序 '{cmd[0]}' 未找到。请确保它在系统PATH中。"
        console.print(f"[bold red]{error_msg}[/]")
        return False, error_msg
    except Exception as e:
        # 捕获 subprocess.run 本身可能发生的错误
        error_msg = f"命令执行时发生意外错误: {str(e)}"
        console.print(f"[bold red]{error_msg}[/]")
        return False, error_msg

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