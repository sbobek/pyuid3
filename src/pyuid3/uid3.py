# AUTOGENERATED! DO NOT EDIT! File to edit: src/uId3.ipynb (unless otherwise specified).

__all__ = ['UId3']

# Cell
from graphviz import Source
from sklearn.base import BaseEstimator

from .attribute import Attribute
from .data import Data
from .entropy_evaluator import EntropyEvaluator
from .uncertain_entropy_evaluator import UncertainEntropyEvaluator
from .tree import Tree
from .tree_node import TreeNode
from .tree_edge import TreeEdge
from .tree_evaluator import TreeEvaluator
from .value import Value
from .reading import Reading
from .instance import Instance

# Cell
class UId3(BaseEstimator):

    def __init__(self, max_depth=2, node_size_limit = 1, grow_confidence_threshold = 0):
        self.TREE_DEPTH_LIMIT= max_depth
        self.NODE_SIZE_LIMIT = node_size_limit
        self.GROW_CONFIDENCE_THRESHOLD = grow_confidence_threshold
        self.tree = None

    def fit(self, data, y=None, *, depth,  entropyEvaluator):   # data should be split into array-like X and y and then fit should be 'fit(X, y)':
        if len(data.get_instances()) < self.NODE_SIZE_LIMIT:
            return None
        if depth > self.TREE_DEPTH_LIMIT:
            return None
        entropy = UncertainEntropyEvaluator().calculate_entropy(data)

        data.update_attribute_domains()

        # of the set is heterogeneous or no attributes to split, just class -- return
        # leaf
        if entropy == 0 or len(data.get_attributes()) == 1:
            # create the only node and summary for it
            class_att = data.get_class_attribute()
            root = TreeNode(class_att.get_name(), data.calculate_statistics(class_att))
            root.set_type(class_att.get_type())
            result = Tree(root)
            return result

        info_gain = 0
        best_split = None
        for a in data.get_attributes():
            if data.get_class_attribute() == a:
                continue
            values = a.get_domain()
            temp_gain = entropy
            temp_numeric_gain = 0
            stats = data.calculate_statistics(a)
            for v in values:
                subdata = None
                subdataLessThan = None
                subdataGreaterEqual = None
                if a.get_type() == Attribute.TYPE_NOMINAL:
                    subdata = data.filter_nominal_attribute_value(a, v)
                elif a.get_type() == Attribute.TYPE_NUMERICAL:
                    subdata_less_than = data.filter_numeric_attribute_value(a, v, True)
                    subdata_greater_equal = data.filter_numeric_attribute_value(a, v, False)

                if a.get_type() == Attribute.TYPE_NOMINAL:
                    temp_gain -= len(subdata)/len(data)*stats.get_stat_for_value(v) * UncertainEntropyEvaluator().calculate_entropy(subdata) #NOT STATS, BUT DS SIZE
                elif a.get_type() == Attribute.TYPE_NUMERICAL:
                    single_temp_gain = entropy - stats.get_stat_for_value(v) * (len(subdata_less_than)/len(data)*UncertainEntropyEvaluator().calculate_entropy(subdata_less_than) + len(subdata_greater_equal)/len(data)*UncertainEntropyEvaluator().calculate_entropy(subdata_greater_equal))
                    if single_temp_gain >= temp_numeric_gain:
                        temp_numeric_gain = single_temp_gain
                        temp_gain = single_temp_gain
                        a.set_value_to_split_on(v)

            if temp_gain >= info_gain:
                info_gain = temp_gain
                best_split = a
                a.set_importance_gain(info_gain)

        # if nothing better can happen
        if best_split == None:
            # create the only node and summary for it
            class_att = data.get_class_attribute()
            root = TreeNode(class_att.get_name(), data.calculate_statistics(class_att))
            root.set_type(class_att.get_type())
            result = Tree(root)
            return result

        # Create root node, and recursively go deeper into the tree.
        class_att = data.get_class_attribute()
        class_stats = data.calculate_statistics(class_att)
        root = TreeNode(best_split.get_name(), class_stats)
        root.set_type(class_att.get_type())

        # attach newly created trees
        for val in best_split.get_splittable_domain():
            if best_split.get_type() == Attribute.TYPE_NOMINAL:
                new_data = data.filter_nominal_attribute_value(best_split, val)
                subtree = self.fit(new_data, entropyEvaluator=EntropyEvaluator, depth=depth + 1)
                best_split_stats = data.calculate_statistics(best_split)
                if subtree and best_split_stats.get_most_probable().get_confidence() > self.GROW_CONFIDENCE_THRESHOLD:
                    root.add_edge(TreeEdge(Value(val, best_split_stats.get_avg_confidence()), subtree.get_root()))
                    root.set_infogain(best_split.get_importance_gain())

            elif best_split.get_type() == Attribute.TYPE_NUMERICAL:
                new_data_less_then = data.filter_numeric_attribute_value(best_split, val, True)
                new_data_greater_equal = data.filter_numeric_attribute_value(best_split, val, False)
                subtree_less_than = self.fit(new_data_less_then, entropyEvaluator=EntropyEvaluator, depth=depth + 1)
                subtree_greater_equal = self.fit(new_data_greater_equal, entropyEvaluator=EntropyEvaluator, depth=depth + 1)
                best_split_stats = data.calculate_statistics(best_split)

                if subtree_less_than and best_split_stats.get_most_probable().get_confidence() > self.GROW_CONFIDENCE_THRESHOLD:
                    root.add_edge(TreeEdge(Value("<" + val, best_split_stats.get_avg_confidence()), subtree_less_than.get_root()))
                if subtree_greater_equal and best_split_stats.get_most_probable().get_confidence() > self.GROW_CONFIDENCE_THRESHOLD:
                    root.add_edge(TreeEdge(Value(">=" + val, best_split_stats.get_avg_confidence()), subtree_greater_equal.get_root()))
                root.set_type(Attribute.TYPE_NUMERICAL)
                root.set_infogain(best_split.get_importance_gain())

        if len(root.get_edges()) == 0:
            root.set_att(data.get_class_attribute().get_name())
            root.set_type(data.get_class_attribute().get_type())

        self.tree = Tree(root)
        return self.tree


    @staticmethod
    def fit_uncertain_nominal() -> None:
        data = Data.parse_uarff("../resources/machine.nominal.uncertain.arff")
        test = Data.parse_uarff("../resources/machine.nominal.uncertain.arff")

        t = UId3.fit(data, UncertainEntropyEvaluator(), 0)
        br = TreeEvaluator.train_and_test(t, test)

        print("###############################################################")
        print(f"Correctly classified instances: {br.get_accuracy() * 100}%")
        print(f"Incorrectly classified instances: {(1-br.get_accuracy()) * 100}%")
        print("TP Rate", "FP Rate", "Precision", "Recall", "F-Measure", "ROC Area", "Class")

        for class_label in data.get_class_attribute().get_domain():
            cs = br.get_stats_for_label(class_label)
            print(cs.get_TP_rate(), cs.get_FP_rate(), cs.get_precision(), cs.get_recall(), cs.get_F_measure(),
                                cs.get_ROC_area(br), cs.get_class_label())

    def predict(self, X):   # should take array-like X -> predict(X)
        if not isinstance(X, (list, np.ndarray)):
            X = [X]
        predictions = []
        for instance in X:
            att_stats = self.tree.predict(instance)
            predictions.append(att_stats.get_most_probable())
        return predictions
