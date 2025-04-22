#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git命令输出捕获测试脚本 - 使用Rich库
测试Rich库是否影响Git命令输出的捕获和显示
"""

import os
import sys
import subprocess
import platform
from typing import List, Tuple, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.prompt import Prompt
except ImportError:
    print("错误: 未安装Rich库，请使用 'pip install rich' 安装")
    sys.exit(1)

try:
    import pyperclip  # 用于复制内容到剪贴板
except ImportError:
    print("提示: pyperclip库未安装，无法使用剪贴板功能")
    print("可以通过运行 'pip install pyperclip' 安装")
    pyperclip = None

# 创建Rich控制台对象
console = Console()

def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到剪贴板
    
    :param text: 要复制的文本
    :return: 是否成功复制
    """
    if pyperclip is None:
        console.print("[bold red]错误:[/] 未安装pyperclip库，无法使用剪贴板功能")
        return False
    
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        console.print(f"[bold red]复制到剪贴板时出错:[/] {str(e)}")
        return False

def test_rich_method1(git_command: List[str]) -> Tuple[bool, str]:
    """
    方法1: 使用subprocess.run + Rich，直接捕获输出
    """
    console.print("\n[bold green]===== 测试方法1: subprocess.run + Rich =====[/]")
    full_cmd = ["git"] + git_command
    cmd_str = " ".join(full_cmd)
    console.print(f"执行命令: [bold cyan]{cmd_str}[/]")
    
    try:
        result = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stdout:
            console.print("\n[bold green]标准输出:[/]")
            # 使用Rich语法高亮显示
            syntax = Syntax(result.stdout, "bash", theme="monokai", line_numbers=False)
            console.print(syntax)
            
        if result.stderr:
            console.print("\n[bold red]错误输出:[/]")
            syntax = Syntax(result.stderr, "bash", theme="monokai", line_numbers=False)
            console.print(syntax)
            
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        console.print(f"[bold red]执行命令时出错:[/] {str(e)}")
        return False, str(e)

def test_rich_method2(git_command: List[str]) -> Tuple[bool, str]:
    """
    方法2: 使用subprocess.Popen + Rich，实时输出
    """
    console.print("\n[bold green]===== 测试方法2: subprocess.Popen + Rich 实时输出 =====[/]")
    full_cmd = ["git"] + git_command
    cmd_str = " ".join(full_cmd)
    console.print(f"执行命令: [bold cyan]{cmd_str}[/]")
    
    full_output = ""
    process = None
    
    try:
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合并标准输出和错误输出
            universal_newlines=False,  # 使用字节流
            bufsize=1  # 行缓冲
        )
        
        if process.stdout:
            console.print("\n[bold green]命令输出:[/]")
            with console.status("[bold green]执行中...[/]") as status:
                for line in iter(process.stdout.readline, b''):
                    line_str = line.decode('utf-8', errors='replace')
                    # 使用Rich直接打印
                    console.print(line_str, end="")
                    full_output += line_str
                
        return_code = process.wait()
        return return_code == 0, full_output
    except Exception as e:
        console.print(f"[bold red]执行命令时出错:[/] {str(e)}")
        return False, str(e)
    finally:
        if process and process.poll() is None:
            process.terminate()

def test_rich_method3(git_command: List[str]) -> Tuple[bool, str]:
    """
    方法3: 使用subprocess.check_output + Rich
    """
    console.print("\n[bold green]===== 测试方法3: subprocess.check_output + Rich =====[/]")
    full_cmd = ["git"] + git_command
    cmd_str = " ".join(full_cmd)
    console.print(f"执行命令: [bold cyan]{cmd_str}[/]")
    
    try:
        output = subprocess.check_output(
            full_cmd, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8', 
            errors='replace'
        )
        
        console.print("\n[bold green]命令输出:[/]")
        # 使用Rich面板显示输出
        panel = Panel(output, title=cmd_str, border_style="green")
        console.print(panel)
        
        return True, output
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]命令执行失败 (返回码: {e.returncode}):[/]")
        if e.output:
            panel = Panel(e.output, title=f"错误输出", border_style="red")
            console.print(panel)
        return False, e.output if e.output else str(e)
    except Exception as e:
        console.print(f"[bold red]执行命令时出错:[/] {str(e)}")
        return False, str(e)

def test_rich_clipboard_copy(git_command: List[str]) -> bool:
    """
    测试将git命令复制到剪贴板 + Rich
    """
    console.print("\n[bold green]===== 测试剪贴板复制 + Rich =====[/]")
    full_cmd = "git " + " ".join(git_command)
    console.print(f"要复制的命令: [bold cyan]{full_cmd}[/]")
    
    if copy_to_clipboard(full_cmd):
        console.print("[bold green]命令已复制到剪贴板！[/] 可以粘贴并手动执行")
        return True
    else:
        console.print("[bold red]复制到剪贴板失败[/]")
        return False

def test_rich_batch_file(git_command: List[str]) -> bool:
    """
    创建临时批处理文件并执行 + Rich（仅Windows）
    """
    if platform.system() != "Windows":
        console.print("[bold yellow]此方法仅适用于Windows系统[/]")
        return False
    
    console.print("\n[bold green]===== 测试临时批处理文件 + Rich =====[/]")
    
    # 创建临时批处理文件
    temp_file = "temp_git_cmd.bat"
    with open(temp_file, "w") as f:
        f.write(f"@echo off\n")
        f.write(f"echo 正在执行Git命令: git {' '.join(git_command)}\n")
        f.write(f"echo --------------------------------------\n")
        f.write(f"git {' '.join(git_command)}\n")
        f.write(f"echo --------------------------------------\n")
        f.write(f"echo 命令执行完毕\n")
        f.write(f"pause\n")  # 使窗口停留
    
    console.print(f"已创建临时批处理文件: [cyan]{temp_file}[/]")
    
    with console.status("[bold green]正在执行批处理文件...[/]") as status:
        # 使用os.system执行批处理文件
        os.system(temp_file)
    
    # 删除临时文件
    os.remove(temp_file)
    console.print(f"批处理文件执行完毕，临时文件 [cyan]{temp_file}[/] 已删除")
    return True

def main():
    """主函数"""
    console.print("[bold cyan]Git命令输出捕获测试 - Rich版[/]")
    console.print("[bold cyan]========================[/]\n")
    
    # 默认测试命令
    default_commands = [
        ["--version"],
        ["status"],
        ["log", "--oneline", "-n", "5"],
        ["branch"]
    ]
    
    # 让用户选择要测试的git命令
    console.print("[bold yellow]请选择要测试的git命令:[/]")
    for i, cmd in enumerate(default_commands):
        console.print(f"[green]{i+1}.[/] git {' '.join(cmd)}")
    console.print(f"[green]{len(default_commands)+1}.[/] 自定义命令")
    
    try:
        choice = int(Prompt.ask("\n请输入命令编号", default="1"))
        if 1 <= choice <= len(default_commands):
            git_command = default_commands[choice-1]
        else:
            custom_cmd = Prompt.ask("请输入git命令参数", default="status -s")
            git_command = custom_cmd.split()
    except ValueError:
        console.print("[bold yellow]输入无效，使用默认命令 'git status'[/]")
        git_command = ["status"]
    except IndexError:
        console.print("[bold yellow]命令编号无效，使用默认命令 'git status'[/]")
        git_command = ["status"]
    
    # 测试不同的方法
    test_rich_method1(git_command)
    test_rich_method2(git_command)
    test_rich_method3(git_command)
    
    # 测试复制到剪贴板
    test_rich_clipboard_copy(git_command)
    
    # 在Windows上测试批处理文件
    if platform.system() == "Windows":
        if Prompt.ask("\n是否要测试批处理文件方法?", choices=["y", "n"], default="n") == "y":
            test_rich_batch_file(git_command)
    
    console.print("\n[bold cyan]========================[/]")
    console.print("[bold green]测试完成！[/]")

if __name__ == "__main__":
    main()