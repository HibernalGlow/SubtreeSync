#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
控制台单例模块
提供全局共享的Rich控制台实例
"""

import sys
from rich.console import Console

# 创建全局单例的Rich控制台对象
console = Console()

def init_console():
    """初始化控制台设置（如果需要）"""
    # 此处可以添加控制台配置，如颜色主题、宽度等
    pass