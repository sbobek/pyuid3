# AUTOGENERATED! DO NOT EDIT! File to edit: src/reading.ipynb (unless otherwise specified).

__all__ = ['Reading']

# Cell
from uid3.attribute import Attribute

# Cell
class Reading:
    def __init__(self, base_att: Attribute, values: list):
        self.base_att = base_att
        self.values = values

    def get_baase_att(self) -> Attribute:
        return self.base_att

    def get_Values(self) -> list:
        return self.values
