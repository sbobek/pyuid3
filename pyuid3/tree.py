# AUTOGENERATED! DO NOT EDIT! File to edit: src/tree.ipynb (unless otherwise specified).

__all__ = ['Condition']

# Cell
from uid3.tree_node import TreeNode
from uid3.value import Value

# Cell
class Condition:
    def __init__(self, att_name: str, value: Value, op='eq'):
        self.attName = attName
        self.value = value
        self.op = op