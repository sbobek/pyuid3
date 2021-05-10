# AUTOGENERATED! DO NOT EDIT! File to edit: src/uncertain_entropy_evaluator.ipynb (unless otherwise specified).

__all__ = ['UncertainEntropyEvaluator']

# Cell
import math

from .data import Data
from .entropy_evaluator import EntropyEvaluator

# Cell
class UncertainEntropyEvaluator(EntropyEvaluator):

    def calculate_entropy(self, data: Data) -> float:
        class_att = data.get_attributes().get_last()
        probs = data.calculate_statistics(class_att)
        entropy = 0
        for v in probs.get_statistics():
            if v.get_confidence() == 0:
                continue
            entropy -= v.get_confidence() * math.log(v.get_confidence()) / math.log(2.0)

        return entropy