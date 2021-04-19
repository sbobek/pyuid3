# AUTOGENERATED! DO NOT EDIT! File to edit: src/tree_node.ipynb (unless otherwise specified).

__all__ = ['TreeNode']

# Cell
from .attribute import Attribute

# Cell
class TreeNode:
    def __init__(self, att_name: str, stats: str):
        self.att = att_name
        self.stats = stats
        self.type = Attribute.TYPE_NOMINAL
        self.infogain = 0

    def get_type(self) -> int:
        return type_of_node

    def set_type(self, type_of_node: int) -> None:
        self.type = type_of_node

    def get_infogain(self) -> float:
        return infogain

    def set_infogain(self, infogain: float) -> None:
        self.infogain = infogain


    #...