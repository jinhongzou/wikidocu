
from typing import Dict, List, Optional, TypedDict, Any
from pathlib import Path
from treelib import Tree

class DirectoryTreeGenerator:
    def __init__(self, root_path: str):
        """
        初始化目录树生成器。
        
        :param root_path: 根目录路径
        """
        self.root_path = Path(root_path)
        if not self.root_path.exists():
            raise FileNotFoundError(f"指定的路径不存在: {root_path}")

    def generate_tree(
        self,
        include_hidden: bool = False,
        include_extensions: Optional[List[str]] = None
    ) -> str:
        """
        生成并返回目录树的字符串表示。

        :param include_hidden: 是否包含隐藏文件/目录（以 '.' 开头）
        :param include_extensions: 允许显示的文件扩展名列表，如 [".py", ".md"]，None 表示显示所有文件
        :return: 目录树的字符串表示
        """
        tree = Tree()
        self._build_treelib(
            path=self.root_path,
            tree=tree,
            include_hidden=include_hidden,
            include_extensions=include_extensions
        )
        tree_str=str(tree)
        tree_str=f"{self.root_path}\n"+'\n'.join(tree_str.splitlines()[1:])
        return tree_str

    def _build_treelib(
        self,
        path: Path,
        tree: Tree,
        parent=None,
        include_hidden: bool = False,
        include_extensions: Optional[List[str]] = None
    ):
        """
        递归构建 treelib 树结构。
        
        :param path: 当前处理的路径
        :param tree: treelib.Tree 实例
        :param parent: 父节点 ID
        :param include_hidden: 是否包含隐藏项
        :param include_extensions: 允许显示的扩展名列表
        """
        # 跳过隐藏文件/目录（如果设置为不包含）
        if not include_hidden and path.name.startswith('.'):
            return

        # 如果是文件，并且设置了扩展名过滤，则检查后缀
        if path.is_file() and include_extensions is not None:
            if path.suffix not in include_extensions:
                return

        node_id = str(path.resolve())
        tree.create_node(tag=path.name, identifier=node_id, parent=parent)

        # 如果是目录，递归处理子项
        if path.is_dir():
            try:
                for child in sorted(path.iterdir()):
                    self._build_treelib(
                        child,
                        tree,
                        parent=node_id,
                        include_hidden=include_hidden,
                        include_extensions=include_extensions
                    )
            except PermissionError:
                pass  # 忽略无权限访问的目录
