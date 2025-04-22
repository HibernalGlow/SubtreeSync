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
    执行命令并实时输出结果，强制UTF-8解码并禁用markup/highlight。
    :param cmd: 命令列表
    :param show_command: 是否显示执行的命令
    :return: (成功标志, 完整输出结果)
    """
    if show_command:
        cmd_str = " ".join(cmd)
        console.print(f"[dim]$ {cmd_str}[/]")

    full_stdout = ""
    full_stderr = ""
    process = None

    try:
        # 使用 Popen 获取字节流，移除 bufsize=1
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False # 确保 stdout/stderr 是字节流
        )

        # --- 实时处理 stdout ---
        if process.stdout:
            # 使用 io.BufferedReader 读取字节流
            stdout_reader = io.BufferedReader(process.stdout)
            while True:
                line_bytes = stdout_reader.readline()
                if not line_bytes: # readline 返回空字节串表示EOF
                    break
                try:
                    # 解码并打印，禁用 Rich 特性
                    line_str = line_bytes.decode('utf-8', errors='replace').rstrip()
                    console.print(line_str, markup=False, highlight=False)
                    full_stdout += line_str + "\n"
                except Exception as e:
                    console.print(f"[bold red]Error processing stdout line: {e}[/]")
                    console.print(f"[dim]Raw bytes: {line_bytes!r}[/]")
            process.stdout.close() # 关闭流

        # --- 处理 stderr (通常在最后读取) ---
        stderr_str = ""
        if process.stderr:
            stderr_bytes = process.stderr.read() # 读取所有剩余的 stderr
            if stderr_bytes:
                try:
                    stderr_str = stderr_bytes.decode('utf-8', errors='replace')
                    if stderr_str:
                        # 打印 stderr
                        with io.StringIO(stderr_str) as f:
                            for line in f:
                                console.print(f"[red]{line.rstrip()}[/]", markup=False, highlight=False)
                        full_stderr += stderr_str
                except Exception as e:
                    console.print(f"[bold red]Error processing stderr: {e}[/]")
                    console.print(f"[dim]Raw stderr bytes: {stderr_bytes!r}[/]")
            process.stderr.close() # 关闭流

        # --- 等待进程结束 ---
        process.wait()
        return_code = process.returncode

        # 合并完整输出
        output = full_stdout + full_stderr

        return return_code == 0, output.strip()

    except FileNotFoundError:
        error_msg = f"错误: 命令或程序 '{cmd[0]}' 未找到。请确保它在系统PATH中。"
        console.print(f"[bold red]{error_msg}[/]")
        return False, error_msg
    except Exception as e:
        error_msg = f"命令执行时发生意外错误: {str(e)}"
        console.print(f"[bold red]{error_msg}[/]")
        # 清理
        if process and process.stdout: process.stdout.close()
        if process and process.stderr: process.stderr.close()
        return False, error_msg
    finally:
        # 确保进程终止
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass

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