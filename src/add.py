#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 添加功能
实现添加新的 git subtree 的功能
"""

import sys
import re
from pathlib import Path
from typing import Dict, Optional

try:
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.table import Table
    from rich.syntax import Syntax
except ImportError:
    print("请先安装Rich库: pip install rich")
    sys.exit(1)

from .utils import (
    console, run_command, validate_git_repo, check_working_tree,
    load_subtree_repos, save_subtree_repo, extract_repo_name
)

def handle_working_tree_changes() -> bool:
    """处理工作区未提交的更改"""
    console.print("[bold yellow]警告:[/] 检测到工作区有未提交的修改")
    
    # 显示当前修改
    success, status_output = run_command(["git", "status", "-s"])
    if success and status_output.strip():
        console.print(Panel(status_output.strip(), title="未提交的更改", border_style="yellow"))
    
    # 提供解决方案选项
    console.print("[bold]解决方案:[/]")
    console.print("1. [green]自动提交当前更改[/] (git add . && git commit -m 'Auto commit before adding subtree')")
    console.print("2. [yellow]暂存当前更改[/] (git stash)")
    console.print("3. [red]取消操作[/] (退出脚本)")
    
    choice = Prompt.ask("[bold cyan]请选择解决方案[/]", choices=["1", "2", "3"], default="3")
    
    if choice == "1":
        # 自动提交
        commit_msg = Prompt.ask("[bold cyan]请输入提交信息[/]", default="Auto commit before adding subtree")
        console.print("[bold blue]提交更改中...[/]")
        add_success, _ = run_command(["git", "add", "."])
        if add_success:
            commit_success, commit_output = run_command(["git", "commit", "-m", commit_msg])
            if commit_success:
                console.print("[bold green]更改已成功提交[/]")
                return True
            else:
                console.print(f"[bold red]提交失败:[/] {commit_output}")
                return False
        else:
            console.print("[bold red]暂存更改失败[/]")
            return False
    
    elif choice == "2":
        # 暂存更改
        console.print("[bold blue]暂存更改中...[/]")
        stash_success, stash_output = run_command(["git", "stash", "save", "Stashed before adding subtree"])
        if stash_success:
            console.print("[bold green]更改已成功暂存[/]")
            console.print("[cyan]提示: 操作完成后可使用 'git stash pop' 恢复暂存的更改[/]")
            return True
        else:
            console.print(f"[bold red]暂存失败:[/] {stash_output}")
            return False
    
    else:
        # 取消操作
        console.print("[yellow]操作已取消[/]")
        return False

def select_existing_repo() -> Optional[Dict[str, str]]:
    """选择已有的仓库配置"""
    repos = load_subtree_repos()
    
    if not repos:
        console.print("[yellow]没有找到已保存的仓库配置[/]")
        return None
    
    console.print("[bold]已保存的仓库配置:[/]")
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
    
    console.print(table)
    
    choice = IntPrompt.ask(
        "[bold cyan]请选择仓库编号[/] (0 表示不选择并继续添加新仓库)",
        choices=[str(i) for i in range(len(repos) + 1)],
        default=0
    )
    
    if choice == 0:
        return None
    
    return repos[choice - 1]

def add_to_taskfile(prefix: str, remote: str, branch: str) -> bool:
    """将新的subtree添加到Taskfile.yml配置中"""
    import re
    
    taskfile_path = Path("Taskfile.yml")
    if not taskfile_path.exists():
        console.print(f"[bold red]错误:[/] 找不到Taskfile.yml文件")
        return False
    
    try:
        with open(taskfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定位SUBTREES部分
        subtrees_pattern = r'(SUBTREES:\s*)((?:[ \t]*-.*\n)*)'
        match = re.search(subtrees_pattern, content)
        
        if not match:
            console.print("[bold red]错误:[/] 在Taskfile.yml中找不到SUBTREES部分")
            return False
        
        # 准备新的条目
        new_entry = f'    - {{ prefix: "{prefix}", remote: "{remote}", branch: "{branch}" }}\n'
        
        # 插入新条目
        existing_subtrees = match.group(2)
        updated_subtrees = match.group(1) + existing_subtrees + new_entry
        
        # 更新文件内容
        updated_content = content.replace(match.group(0), updated_subtrees)
        
        with open(taskfile_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        console.print(f"已将新subtree添加到Taskfile.yml", style="green")
        return True
    
    except Exception as e:
        console.print(f"[bold red]更新Taskfile.yml时出错:[/] {str(e)}")
        return False

def add_subtree(args=None) -> bool:
    """交互式添加git subtree"""
    console.print(Panel.fit("[bold green]Git Subtree 添加工具", 
                           border_style="green", 
                           title="GlowToolBox", 
                           subtitle="v1.0"))
    
    # 检查是否在git仓库中
    if not validate_git_repo():
        console.print("[bold red]错误:[/] 当前目录不是git仓库。请在git仓库根目录下运行此脚本。")
        return False
    
    # 检查工作区是否有未提交的更改
    if check_working_tree():
        if not handle_working_tree_changes():
            return False
    
    # 如果传入了参数，直接使用
    if args and args.remote and args.name and args.prefix:
        remote = args.remote
        repo_name = args.name
        prefix = args.prefix
        branch = args.branch or "main"
    else:
        # 询问是否使用已有仓库
        use_existing = Confirm.ask("[bold cyan]是否使用已保存的仓库配置?[/]", default=False)
        
        selected_repo = None
        if use_existing:
            selected_repo = select_existing_repo()
            if selected_repo:
                remote = selected_repo.get("remote", "")
                repo_name = selected_repo.get("name", "")
                prefix = selected_repo.get("prefix", "")
                branch = selected_repo.get("branch", "main")
            else:
                # 用户选择了不使用已有仓库，继续添加新仓库
                pass
        
        if not selected_repo:
            # 输入远程仓库
            remote = Prompt.ask("[bold cyan]请输入远程仓库地址[/] (例如 https://github.com/user/repo.git)")
            if not remote:
                console.print("[bold red]错误:[/] 远程仓库地址不能为空")
                return False
            
            # 自动提取项目名作为本地仓库名
            suggested_name = extract_repo_name(remote)
            
            # 输入本地仓库名
            repo_name = Prompt.ask(
                "[bold cyan]请输入本地仓库名[/] (用于引用远程仓库)",
                default=suggested_name if suggested_name else None
            )
            if not repo_name:
                console.print("[bold red]错误:[/] 本地仓库名不能为空")
                return False
            
            # 自动构建本地目录前缀
            suggested_prefix = f"src/projects/{repo_name}"
            
            # 输入本地前缀
            prefix = Prompt.ask(
                "[bold cyan]请输入本地目录前缀[/]",
                default=suggested_prefix
            )
            if not prefix:
                console.print("[bold red]错误:[/] 本地目录前缀不能为空")
                return False
            
            # 输入分支名，默认为main
            branch = Prompt.ask("[bold cyan]请输入分支名[/]", default="main")
    
    # 确认信息
    console.print("\n[bold]===确认信息===", style="cyan")
    
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("键", style="bold cyan")
    table.add_column("值")
    
    table.add_row("远程仓库地址", remote)
    table.add_row("本地仓库名", repo_name)
    table.add_row("本地目录前缀", prefix)
    table.add_row("分支名称", branch)
    
    console.print(table)
    
    # 如果不是命令行模式，需要确认
    if not args or not args.yes:
        if not Confirm.ask("\n是否继续?"):
            console.print("操作已取消", style="yellow")
            return False
    
    # 添加远程仓库 - 显示完整命令
    console.print(f"\n[bold blue]添加远程仓库:[/] {repo_name} -> {remote}")
    add_remote_cmd = ["git", "remote", "add", repo_name, remote]
    remote_success, remote_output = run_command(add_remote_cmd)
    
    if not remote_success:
        # 检查是否已存在
        check_remote_cmd = ["git", "remote", "get-url", repo_name]
        check_success, check_output = run_command(check_remote_cmd)
        
        if check_success:
            console.print(f"远程仓库 '[bold]{repo_name}[/]' 已存在，URL: {check_output.strip()}")
            if check_output.strip() != remote:
                console.print(f"[bold yellow]警告:[/] 现有远程仓库URL与您输入的不同!")
                if Confirm.ask(f"是否更新远程仓库 '{repo_name}' 的URL?"):
                    update_cmd = ["git", "remote", "set-url", repo_name, remote]
                    update_success, update_output = run_command(update_cmd)
                    if update_success:
                        console.print(f"已更新远程仓库URL", style="green")
                    else:
                        console.print(f"[bold red]更新远程仓库URL失败:[/] {update_output}")
                        return False
        else:
            console.print(f"[bold red]添加远程仓库失败:[/] {remote_output}")
            return False
    else:
        console.print("远程仓库添加成功", style="green")
    
    # 执行git subtree add命令 - 显示完整命令
    console.print(f"\n[bold blue]添加subtree:[/] {prefix} <- {repo_name}/{branch}")
    cmd = ["git", "subtree", "add", f"--prefix={prefix}", repo_name, branch, "--squash"]
    
    # 显示完整命令
    cmd_str = " ".join(cmd)
    console.print(Panel(Syntax(cmd_str, "bash", theme="monokai"), 
                       title="完整Git命令", 
                       border_style="blue"))
    
    success, output = run_command(cmd, show_command=False)  # 已经显示了命令，不需要再显示
    
    if success:
        console.print("[bold green]Subtree添加成功![/]")
        console.print(Panel(output.strip(), border_style="green", title="命令输出"))
        
        # 保存仓库配置
        from datetime import datetime
        repo_info = {
            "name": repo_name,
            "remote": remote,
            "prefix": prefix,
            "branch": branch,
            "added_time": datetime.now().isoformat(),
            "extra": {}  # 预留扩展空间
        }
        
        if save_subtree_repo(repo_info):
            console.print("[green]已保存仓库配置到本地[/]")
        
        # 询问是否添加到Taskfile.yml
        if not args or not args.no_taskfile:
            add_to_taskfile_flag = True
            if not args or not args.yes:
                add_to_taskfile_flag = Confirm.ask("\n是否将此subtree添加到Taskfile.yml?", default=True)
            if add_to_taskfile_flag:
                add_to_taskfile(prefix, remote, branch)
        
        return True
    else:
        console.print("[bold red]Subtree添加失败:[/]")
        console.print(Panel(output.strip(), border_style="red", title="错误输出"))
        
        # 检查是否因为工作区有修改而失败
        if "working tree has modifications" in output:
            console.print("[bold yellow]原因:[/] 工作区有未提交的修改")
            if Confirm.ask("是否尝试处理未提交的更改并重试?"):
                if handle_working_tree_changes():
                    # 重试添加subtree
                    console.print(f"\n[bold blue]重试添加subtree:[/] {prefix} <- {repo_name}/{branch}")
                    retry_success, retry_output = run_command(cmd)
                    if retry_success:
                        console.print("[bold green]Subtree添加成功![/]")
                        console.print(Panel(retry_output.strip(), border_style="green", title="命令输出"))
                        
                        # 保存仓库配置
                        from datetime import datetime
                        repo_info = {
                            "name": repo_name,
                            "remote": remote,
                            "prefix": prefix,
                            "branch": branch,
                            "added_time": datetime.now().isoformat(),
                            "extra": {}  # 预留扩展空间
                        }
                        
                        if save_subtree_repo(repo_info):
                            console.print("[green]已保存仓库配置到本地[/]")
                        
                        # 询问是否添加到Taskfile.yml
                        if not args or not args.no_taskfile:
                            add_to_taskfile_flag = True
                            if not args or not args.yes:
                                add_to_taskfile_flag = Confirm.ask("\n是否将此subtree添加到Taskfile.yml?", default=True)
                            if add_to_taskfile_flag:
                                add_to_taskfile(prefix, remote, branch)
                        
                        return True
                    else:
                        console.print("[bold red]重试添加subtree失败:[/]")
                        console.print(Panel(retry_output.strip(), border_style="red", title="错误输出"))
        
        return False