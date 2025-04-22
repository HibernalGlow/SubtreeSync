#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Subtree 同步工具 - 主入口
这是一个简单的包装器，调用实际的实现脚本
"""

import sys
import os
from pathlib import Path

# 获取当前脚本所在目录
SCRIPT_DIR = Path(__file__).resolve().parent

def main():
    """主函数，调用子模块"""
    # 调用主实现脚本
    subtree_sync_script = SCRIPT_DIR / "subtree-sync.py"
    if subtree_sync_script.exists():
        # 将参数传递给实际的脚本
        cmd = [sys.executable, str(subtree_sync_script)] + sys.argv[1:]
        os.execv(sys.executable, cmd)
    else:
        print(f"错误: 找不到 subtree-sync.py 文件，请检查安装")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)