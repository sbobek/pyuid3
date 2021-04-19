# AUTOGENERATED! DO NOT EDIT! File to edit: src/tree.ipynb (unless otherwise specified).

__all__ = ['Tree', 'Condition']

# Cell
from .tree_node import TreeNode
from .value import Value

# Cell
class Tree:
    def __init__(self, root: TreeNode):
        set_root(root)

    def get_root(self) -> TreeNode:
        return self.root

    def set_root(self, root: TreeNode) -> None:
        self.root = root

# Cell
class Condition:
    def __init__(self, att_name: str, value: Value, op='eq'):
        self.attName = attName
        self.value = value
        self.op = op