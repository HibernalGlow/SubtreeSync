# SubtreeSync

Git Subtree 管理工具，用于简化 Git Subtree 的添加、同步和维护操作。

## 功能

- **添加子树**: 交互式添加新的 git subtree，自动处理常见问题
- **拉取更新**: 从远程仓库拉取子树更新，支持拉取所有或特定子树
- **推送更新**: 将本地子树更改推送到远程仓库，支持推送所有或特定子树
- **列出子树**: 显示所有已配置的子树信息，支持详细信息查看

## 安装

确保已安装以下依赖：

```bash
pip install rich
```

## 使用方法

### 添加子树

```bash
python main.py add
```

交互式添加一个 Git 子树，会引导你输入远程仓库地址、本地目录前缀等信息。

也可以直接指定参数：

```bash
python main.py add --remote https://github.com/user/repo.git --name repo_name --prefix src/projects/repo_name
```

### 拉取更新

拉取所有子树更新：

```bash
python main.py pull
```

拉取特定子树更新：

```bash
python main.py pull --name repo_name
```

### 推送更新

推送所有子树更新：

```bash
python main.py push
```

推送特定子树更新：

```bash
python main.py push --name repo_name
```

### 列出子树

列出所有配置的子树：

```bash
python main.py list
```

显示详细信息：

```bash
python main.py list --verbose
```

## 项目结构

```
SubtreeSync/
│
├── main.py                 # 主入口文件
├── subtree-sync.py         # 命令行接口实现
├── README.md               # 项目说明文档
├── subtree_repos.json      # 子树仓库配置文件
│
└── src/                    # 源代码目录
    ├── __init__.py         # 包初始化文件
    ├── add.py              # 添加子树功能
    ├── pull.py             # 拉取子树更新功能
    ├── push.py             # 推送子树更新功能 
    ├── list.py             # 列出子树功能
    └── utils.py            # 通用工具函数
```

## 参考

- 基于 [GwendolenLynch/git-subtree-sync](https://github.com/GwendolenLynch/git-subtree-sync) 项目改进而来
- Git Subtree 文档：[Git Tools - Subtree Merging](https://git-scm.com/book/en/v2/Git-Tools-Advanced-Merging#_subtree_merge)
