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
    script_dir = Path(__file__).resolve().parent
    return script_dir

def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_config_dir() / "subtree_repos.json"

def ensure_config_exists():
    """确保配置文件存在"""
    config_path = get_config_path()
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # 初始化多仓库配置结构
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"repositories": [], "current_repository": None}, f, ensure_ascii=False, indent=2)

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    ensure_config_exists()
    try:
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 确保新的配置格式存在
            if "repositories" not in config:
                # 兼容旧格式，创建新格式
                if "repos" in config:
                    # 将旧格式转换为新格式
                    config = {
                        "repositories": [
                            {
                                "name": "Default",
                                "path": ".",
                                "is_default": True,
                                "repos": config.get("repos", [])
                            }
                        ],
                        "current_repository": "Default"
                    }
                else:
                    # 创建空的新格式
                    config = {"repositories": [], "current_repository": None}
            return config
    except Exception as e:
        console.print(f"[bold red]读取配置文件失败:[/] {str(e)}")
        return {"repositories": [], "current_repository": None}

def save_config(config: Dict[str, Any]) -> bool:
    """保存配置文件"""
    try:
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        console.print(f"[bold red]保存配置文件失败:[/] {str(e)}")
        return False

def load_all_repositories() -> List[Dict[str, Any]]:
    """加载所有仓库配置"""
    config = load_config()
    return config.get("repositories", [])

def get_current_repository_name() -> Optional[str]:
    """获取当前选中的仓库名称"""
    config = load_config()
    return config.get("current_repository")

def get_default_repository() -> Optional[Dict[str, Any]]:
    """获取默认的仓库配置"""
    repositories = load_all_repositories()
    for repo in repositories:
        if repo.get("is_default", False):
            return repo
    return repositories[0] if repositories else None

def get_current_repository() -> Optional[Dict[str, Any]]:
    """获取当前选中的仓库配置"""
    current_name = get_current_repository_name()
    if not current_name:
        return get_default_repository()
        
    repositories = load_all_repositories()
    for repo in repositories:
        if repo.get("name") == current_name:
            return repo
    
    # 如果当前仓库不存在，返回默认仓库
    return get_default_repository()

def set_current_repository(name: str) -> bool:
    """设置当前选中的仓库"""
    config = load_config()
    config["current_repository"] = name
    return save_config(config)

def load_subtree_repos() -> List[Dict[str, Any]]:
    """加载当前仓库的子树配置"""
    repo = get_current_repository()
    if not repo:
        console.print("[bold yellow]警告:[/] 未设置当前仓库或无仓库配置")
        return []
    return repo.get("repos", [])

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
    从当前仓库配置中删除subtree仓库配置
    
    Args:
        name: 仓库名称
        
    Returns:
        是否成功删除
    """
    current_repo = get_current_repository()
    if not current_repo:
        console.print("[bold red]错误:[/] 未设置当前仓库")
        return False
    
    repos = current_repo.get("repos", [])
    initial_count = len(repos)
    
    # 过滤掉要删除的仓库
    repos = [repo for repo in repos if repo.get("name") != name]
    
    if len(repos) == initial_count:
        # 没有找到要删除的仓库
        return False
    
    # 更新当前仓库的子树列表
    current_repo["repos"] = repos
    
    # 更新整体配置
    config = load_config()
    for i, repo in enumerate(config.get("repositories", [])):
        if repo.get("name") == current_repo.get("name"):
            config["repositories"][i] = current_repo
            break
    
    return save_config(config)

def save_subtree_repo(repo_info: Dict[str, str]) -> bool:
    """保存subtree仓库配置到当前选中的仓库中"""
    current_repo = get_current_repository()
    if not current_repo:
        console.print("[bold red]错误:[/] 未设置当前仓库")
        return False
    
    repos = current_repo.get("repos", [])
    
    # 检查是否已存在
    for i, repo in enumerate(repos):
        if repo.get("name") == repo_info["name"]:
            # 更新已存在的配置
            repos[i] = repo_info
            break
    else:
        # 添加新配置
        repos.append(repo_info)
    
    # 更新当前仓库的子树列表
    current_repo["repos"] = repos
    
    # 更新整体配置
    config = load_config()
    for i, repo in enumerate(config.get("repositories", [])):
        if repo.get("name") == current_repo.get("name"):
            config["repositories"][i] = current_repo
            break
    
    return save_config(config)

def add_repository(repo_info: Dict[str, Any]) -> bool:
    """添加或更新仓库配置"""
    config = load_config()
    repositories = config.get("repositories", [])
    
    # 检查是否已存在
    for i, repo in enumerate(repositories):
        if repo.get("name") == repo_info["name"]:
            # 更新已存在的配置
            repositories[i] = repo_info
            break
    else:
        # 添加新配置
        repositories.append(repo_info)
    
    config["repositories"] = repositories
    
    # 如果只有一个仓库，设为默认和当前仓库
    if len(repositories) == 1:
        repositories[0]["is_default"] = True
        config["current_repository"] = repositories[0]["name"]
    
    return save_config(config)

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

def run_command_direct(cmd: List[str], show_command: bool = True) -> bool:
    """
    执行命令并直接将输出显示在终端上，不捕获输出，避免Rich和编码问题。
    这是处理Git命令的最简单可靠方式。
    
    :param cmd: 命令列表
    :param show_command: 是否显示执行的命令
    :return: 命令是否成功执行
    """
    if show_command:
        cmd_str = " ".join(cmd)
        console.print(f"[dim]$ {cmd_str}[/]")
        
    try:
        # 直接使用subprocess.run，不捕获输出，让它显示在终端上
        result = subprocess.run(
            cmd,
            # 不使用stdout=subprocess.PIPE和stderr=subprocess.PIPE
            # 这样输出会直接显示在终端上
            check=False,  # 不抛出异常，而是通过返回码判断成功与否
            text=True,    # 文本模式
            encoding='utf-8',
            errors='replace'
        )
        
        # 只返回成功与否，不返回输出内容
        return result.returncode == 0
    except FileNotFoundError:
        error_msg = f"错误: 命令或程序 '{cmd[0]}' 未找到。请确保它在系统PATH中。"
        console.print(f"[bold red]{error_msg}[/]")
        return False
    except Exception as e:
        error_msg = f"命令执行时发生意外错误: {str(e)}"
        console.print(f"[bold red]{error_msg}[/]")
        return False

def run_git_command_direct(cmd_args: List[str], show_command: bool = True) -> bool:
    """
    直接执行Git命令，输出显示在终端上，不捕获输出
    
    :param cmd_args: Git命令参数列表
    :param show_command: 是否显示执行的命令
    :return: 命令是否成功执行
    """
    full_cmd = ["git"] + cmd_args
    return run_command_direct(full_cmd, show_command)

# --- GitPython Integration ---

_repo_cache = None

def get_repo() -> Optional[git.Repo]:
    """获取当前目录的 GitPython Repo 对象，带缓存"""
    global _repo_cache
    if (_repo_cache):
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
    使用 subprocess.Popen 执行 Git 命令并实时流式输出结果, 在正确的仓库目录执行。
    :param repo: GitPython Repo 对象 (用于获取工作目录)
    :param command_list: Git 子命令列表 (例如 ['subtree', 'pull', ...])
    :param show_command: 是否显示执行的命令
    :return: (成功标志, 完整输出结果)
    """
    # Prepend 'git' to the command list for execution
    full_cmd = ['git'] + command_list
    if show_command:
        cmd_str = " ".join(full_cmd)
        # Use print for simplicity here, as console might be problematic
        print(f"$ {cmd_str}")

    full_stdout = ""
    full_stderr = ""
    process = None

    try:
        # Use subprocess.Popen directly, setting the working directory
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=repo.working_dir, # Execute in the repository's working directory
            universal_newlines=False # Ensure bytes
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

    # Keep GitCommandError for potential future use if switching back
    except git.GitCommandError as e:
        print(f"Git 命令执行失败: {e.command}")
        print(f"返回码: {e.status}")
        stderr_output = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        print(f"错误输出:\n{stderr_output}")
        return False, stderr_output
    except FileNotFoundError:
        # This error now correctly refers to 'git' if it's not found
        error_msg = f"错误: 命令或程序 '{full_cmd[0]}' 未找到。请确保 Git 已安装并在系统 PATH 中。"
        print(error_msg) # Use print
        return False, error_msg
    except Exception as e:
        error_msg = f"执行 Git 命令时发生意外错误: {str(e)}"
        print(error_msg) # Use print
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