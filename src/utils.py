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
import git # Import GitPython
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
    执行命令并实时输出结果，强制UTF-8解码，绕过rich打印。
    :param cmd: 命令列表
    :param show_command: 是否显示执行的命令
    :return: (成功标志, 完整输出结果)
    """
    if show_command:
        # Still use console.print for the command itself for nice formatting
        cmd_str = " ".join(cmd)
        console.print(f"[dim]$ {cmd_str}[/]")

    full_stdout = ""
    full_stderr = ""
    process = None

    try:
        # 使用 Popen 获取字节流
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False # 确保 stdout/stderr 是字节流
        )

        # --- 实时处理 stdout ---
        if process.stdout:
            stdout_reader = io.BufferedReader(process.stdout)
            while True:
                line_bytes = stdout_reader.readline()
                if not line_bytes:
                    break
                try:
                    # 解码为 UTF-8，替换错误
                    line_str = line_bytes.decode('utf-8', errors='replace')
                    # 直接写入 sys.stdout，不经过 rich
                    sys.stdout.write(line_str)
                    sys.stdout.flush() # 确保立即显示
                    full_stdout += line_str
                except Exception as e:
                    # 如果写入或解码失败，打印错误到 stderr
                    error_msg = f"\n[Error processing stdout line: {e}] Raw bytes: {line_bytes!r}\n"
                    sys.stderr.write(error_msg)
                    sys.stderr.flush()
            process.stdout.close()

        # --- 处理 stderr ---
        stderr_str = ""
        if process.stderr:
            stderr_bytes = process.stderr.read()
            if stderr_bytes:
                try:
                    stderr_str = stderr_bytes.decode('utf-8', errors='replace')
                    if stderr_str:
                        # 直接写入 sys.stderr
                        sys.stderr.write(stderr_str)
                        sys.stderr.flush() # 确保立即显示
                        full_stderr += stderr_str
                except Exception as e:
                    error_msg = f"\n[Error processing stderr: {e}] Raw stderr bytes: {stderr_bytes!r}\n"
                    sys.stderr.write(error_msg)
                    sys.stderr.flush()
            process.stderr.close()

        # --- 等待进程结束 ---
        process.wait()
        return_code = process.returncode

        # 合并完整输出
        output = full_stdout + full_stderr

        return return_code == 0, output.strip() # strip() might remove necessary newlines if output is multi-line

    except FileNotFoundError:
        error_msg = f"错误: 命令或程序 '{cmd[0]}' 未找到。请确保它在系统PATH中。"
        # Use console.print for our own error messages
        console.print(f"[bold red]{error_msg}[/]")
        return False, error_msg
    except Exception as e:
        error_msg = f"命令执行时发生意外错误: {str(e)}"
        console.print(f"[bold red]{error_msg}[/]")
        if process and process.stdout: process.stdout.close()
        if process and process.stderr: process.stderr.close()
        return False, error_msg
    finally:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass

# --- GitPython Integration ---

_repo_cache = None

def get_repo() -> Optional[git.Repo]:
    """获取当前目录的 GitPython Repo 对象，带缓存"""
    global _repo_cache
    if _repo_cache:
        return _repo_cache
    try:
        repo = git.Repo(search_parent_directories=True)
        _repo_cache = repo
        return repo
    except git.InvalidGitRepositoryError:
        print("错误: 当前目录或其父目录不是有效的 Git 仓库。")
        return None
    except Exception as e:
        print(f"初始化 Git 仓库对象时出错: {e}")
        return None

def run_git_command_stream(repo: git.Repo, command_list: List[str], show_command: bool = True) -> Tuple[bool, str]:
    """
    使用 GitPython 执行 Git 命令并实时流式输出结果。
    :param repo: GitPython Repo 对象
    :param command_list: 命令列表 (例如 ['subtree', 'pull', ...])
    :param show_command: 是否显示执行的命令
    :return: (成功标志, 完整输出结果)
    """
    if show_command:
        cmd_str = " ".join(['git'] + command_list) # Prepend 'git' for display
        print(f"$ {cmd_str}")

    full_stdout = ""
    full_stderr = ""
    process = None

    try:
        # 使用 repo.git.execute 获取 Popen 对象
        # 移除 stdout_as_string 和 stderr_as_string
        process = repo.git.execute(
            command_list, # Pass command list directly
            with_stdout=True, # Needed for stdout piping
            as_process=True,
            universal_newlines=False # Get bytes
        )

        # --- 实时处理 stdout (与 run_command 逻辑相同) ---
        if process.stdout:
            stdout_reader = io.BufferedReader(process.stdout)
            while True:
                line_bytes = stdout_reader.readline()
                if not line_bytes:
                    break
                try:
                    line_str = line_bytes.decode('utf-8', errors='replace')
                    sys.stdout.write(line_str)
                    sys.stdout.flush()
                    full_stdout += line_str
                except Exception as e:
                    error_msg = f"\n[Error processing stdout line: {e}] Raw bytes: {line_bytes!r}\n"
                    sys.stderr.write(error_msg)
                    sys.stderr.flush()
            process.stdout.close()

        # --- 处理 stderr (与 run_command 逻辑相同) ---
        stderr_str = ""
        if process.stderr:
            stderr_bytes = process.stderr.read()
            if stderr_bytes:
                try:
                    stderr_str = stderr_bytes.decode('utf-8', errors='replace')
                    if stderr_str:
                        sys.stderr.write(stderr_str)
                        sys.stderr.flush()
                        full_stderr += stderr_str
                except Exception as e:
                    error_msg = f"\n[Error processing stderr: {e}] Raw stderr bytes: {stderr_bytes!r}\n"
                    sys.stderr.write(error_msg)
                    sys.stderr.flush()
            process.stderr.close()

        # --- 等待进程结束 ---
        return_code = process.wait() # Wait for process completion

        output = full_stdout + full_stderr
        return return_code == 0, output.strip()

    except git.GitCommandError as e:
        # GitPython specific error
        print(f"Git 命令执行失败: {e.command}")
        print(f"返回码: {e.status}")
        # Try to decode stderr from the exception if available
        stderr_output = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        print(f"错误输出:\n{stderr_output}")
        return False, stderr_output
    except FileNotFoundError:
        # This might happen if 'git' itself is not found, though less likely via GitPython
        error_msg = f"错误: 命令或程序 'git' 未找到。"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"执行 Git 命令时发生意外错误: {str(e)}"
        print(error_msg)
        # Cleanup process streams if Popen object was created
        if process and process.stdout: process.stdout.close()
        if process and process.stderr: process.stderr.close()
        return False, error_msg
    finally:
        # Ensure process termination (same as run_command)
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass

def validate_git_repo() -> bool:
    """检查当前是否在git仓库中 (使用 GitPython)"""
    return get_repo() is not None

def check_working_tree() -> bool:
    """检查工作区状态，返回是否有未提交的更改 (使用 GitPython)"""
    repo = get_repo()
    if not repo:
        return False # Not a repo, treat as no changes for safety? Or raise error?
    try:
        # is_dirty(untracked_files=True) checks for modified, added, deleted, and untracked files
        return repo.is_dirty(untracked_files=True)
    except Exception as e:
        print(f"检查工作区状态时出错: {e}")
        return True # Assume dirty on error

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
    """获取当前git仓库的所有远程仓库 (使用 GitPython)"""
    repo = get_repo()
    if not repo:
        return []
    try:
        remotes_info = []
        for remote in repo.remotes:
            # Assuming fetch URL is representative, could also check push URL
            url = next(remote.urls, None) # Get first URL
            if url:
                remotes_info.append({
                    "name": remote.name,
                    "url": url
                })
        return remotes_info
    except Exception as e:
        print(f"列出 Git 远程仓库时出错: {e}")
        return []