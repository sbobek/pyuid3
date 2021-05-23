# AUTOGENERATED! DO NOT EDIT! File to edit: src/tree_evaluator.ipynb (unless otherwise specified).

__all__ = ['TreeEvaluator']

# Cell
from .att_stats import AttStats
from .attribute import Attribute
from .data import Data
from .tree import Tree
from .uncertain_entropy_evaluator import UncertainEntropyEvaluator

# Cell
class TreeEvaluator:

    class BenchmarkResult:
        def __init__(self, class_attribute: Attribute):
            self.stats = []
            self.predicitons = []

            self.stats = [class_label for class_label in class_attribute.get_domain()]

        def train_and_test(self, training_data: Data, test_data: Data):
            trained_tree = UId3.grow_tree(trainingData, UncertainEntropyEvaluator(), 0)

            return self.test(trained_tree, test_data)


        def test(trained_tree: 'Tree', test_data: Data):
            result = BenchmarkResult(test_data.get_class_attribute())

            for i in test_data.get_instances():
                prediction = trained_tree.predict(i)
                error =  not prediction.get_most_porbable().get_name() == i.get_readings().get_last().get_most_probable().get_name()
                result.add_prediction(Prediction(prediction, i.get_readings().get_last().get_most_probable().get_name()))
                if error:
                    #give false positive to predicted class, false negative to real class, and true negatives to other
                    predicted_name = prediction.get_most_porbable().get_name()
                    real_name = i.get_readings().get_last().get_most_probable().get_name()
                    result.add_FP(predicted_name)
                    result.add_FN(real_name)
                    for s in result.stats:
                        if not s.class_label == predicted_name and not s.class_label == real_name:
                            result.add_TN(s.get_class_label())
                    result.incorrect += 1
                else:
                    #add true positive for predicted class, and true negatives for other
                    predicted_name = prediction.get_most_porbable().get_name()
                    result.add_TP(predicted_name)
                    for s in result.stats:
                        if not s.class_label == predicted_name:
                            result.add_TN(s.get_class_label())
                    result.correct += 1
            return result

        def get_predictions(self) -> list:
            return predictions

        def get_accuracy(self) -> float:
            return correct / (correct + incorrect)

        def get_stats_for_label(self, class_label: str):
            for s in self.stats:
                if s.get_class_label() == class_label:
                    return s
            return None

        def add_TP(self, value: str) -> None:
            for s in self.stats:
                if s.get_class_label() == value:
                    s.set_TP(s.get_TP() + 1)
                    break

        def add_FP(self, value: str) -> None:
            for s in self.stats:
                if s.get_class_label() == value:
                    s.set_FP(s.get_FP() + 1)
                    break

        def add_TN(self, value: str) -> None:
            for s in self.stats:
                if s.get_class_label() == value:
                    s.set_TN(s.get_TN() + 1)
                    break

        def add_FN(self, value: str) -> None:
            for s in self.stats:
                if s.get_class_label() == value:
                    s.set_FN(s.get_FN() + 1)
                    break

        def add_prediction(self, prediction) -> None:
            predictions.append(prediction)

    class Prediction:
        def __init__(self, prediction: AttStats, correct_label: str):
            self.prediction = prediction
            self.correct_label = correct_label

        def __lt__(self, p1):
            prob1 = self.prediction.get_stat_for_value(class_label)
            prob2 = p1.prediction.get_stat_for_value(class_label)
            return prob1 < prob2

        def __le__(self, p1):
            prob1 = self.prediction.get_stat_for_value(class_label)
            prob2 = p1.prediction.get_stat_for_value(class_label)
            return prob1 <= prob2

        def __eq__(self, p1):
            prob1 = self.prediction.get_stat_for_value(class_label)
            prob2 = p1.prediction.get_stat_for_value(class_label)
            return prob1 == prob2

        def __ne__(self, p1):
            prob1 = self.prediction.get_stat_for_value(class_label)
            prob2 = p1.prediction.get_stat_for_value(class_label)
            return prob1 != prob2

        def __gt__(self, p1):
            prob1 = self.prediction.get_stat_for_value(class_label)
            prob2 = p1.prediction.get_stat_for_value(class_label)
            return prob1 > prob2

        def __ge__(self, p1):
            prob1 = self.prediction.get_stat_for_value(class_label)
            prob2 = p1.prediction.get_stat_for_value(class_label)
            return prob1 >= prob2

    class Stats:
        def __init__(self, class_label):
            self.class_label = class_label

        def get_TP_rate(self) -> float:
            return self.get_TP() / (self.get_TP() + self.get_FN())

        def get_FP_rate(self) -> float:
            return self.get_FP() / (self.get_FP() + self.get_TN())

        def get_precision(self) -> float:
            return self.get_TP() / (self.get_TP() + self.get_FP())

        def get_recall(self) -> float:
            return self.get_TP() / (self.get_TP() + self.get_FN())

        def get_F_measure(self) -> float:
            return 2 * (self.getPrecision() * self.getRecall()) / (self.getPrecision() + self.getRecall())

        def get_ROC_area(bench) -> float:
            result = 0
            preds = bench.get_predictions()

            preds = sorted(preds)

            n_class_count = 0
            y_class_count = 0
            uy  = 0
            un = 0
            for p in preds:
                if p.correct_label == class_label:
                    uy += n_class_count
                    y_class_count += 1
                else:
                    un += y_class_count
                    n_class_count += 1

            result = uy / (uy + un)
            return result

        def get_class_label(self) -> str:
            return class_label

        def set_class_label(class_label: str) -> None:
            self.class_label = class_label

        def get_TP(self) -> float:
            return TP

        def set_TP(self, TP: float) -> None:
            self.TP = TP

        def get_FP(self) -> float:
            return FP

        def set_FP(self, FP: float) -> None:
            self.FP = FP

        def get_TN(self) -> float:
            return TN

        def set_TN(self, TN: float) -> None:
            self.TN = TN

        def get_FN(self) -> float:
            return FN

        def set_FN(self, FN: float) -> None:
            self.FN = FN
