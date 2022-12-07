# AUTOGENERATED! DO NOT EDIT! File to edit: src/uId3.ipynb (unless otherwise specified).

__all__ = ['UId3']

# Cell
from graphviz import Source
from sklearn.base import BaseEstimator
import numpy as np
import pandas as pd

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
from multiprocessing import cpu_count,Pool

# Cell
class UId3(BaseEstimator):

    def __init__(self, max_depth=2, node_size_limit = 1, grow_confidence_threshold = 0, min_impurity_decrease=0):
        self.TREE_DEPTH_LIMIT= max_depth
        self.NODE_SIZE_LIMIT = node_size_limit
        self.GROW_CONFIDENCE_THRESHOLD = grow_confidence_threshold
        self.tree = None
        self.node_size_limit = node_size_limit
        self.min_impurity_decrease=min_impurity_decrease

    def fit(self, data, y=None, *, depth,  entropyEvaluator, beta=1, n_jobs=None):   # data should be split into array-like X and y and then fit should be 'fit(X, y)':
        if len(data.get_instances()) < self.NODE_SIZE_LIMIT:
            return None
        if depth > self.TREE_DEPTH_LIMIT:
            return None
        entropy = entropyEvaluator.calculate_entropy(data)

        data.update_attribute_domains()

        # of the set is heterogeneous or no attributes to split, just class -- return
        # leaf
        if entropy == 0 or len(data.get_attributes()) == 1:
            # create the only node and summary for it
            class_att = data.get_class_attribute()
            root = TreeNode(class_att.get_name(), data.calculate_statistics(class_att))
            root.set_type(class_att.get_type())
            tree = Tree(root)
            if depth == 0:
                self.tree = tree
            return tree

        info_gain = 0
        best_split = None
        
        
        cl=[]
        for i in data.get_instances():
            cl.append(i.get_reading_for_attribute(data.get_class_attribute()).get_most_probable().get_name())
        
        for a in data.get_attributes():
            if data.get_class_attribute() == a:
                continue
                
            values = a.get_domain()
            pure_info_gain = 0
            stats = data.calculate_statistics(a)
            
            ## start searching for best border values  -- such that class value remains the same for the ranges between them
            if a.get_type() == Attribute.TYPE_NUMERICAL:
                border_search_list = []
                for i in data.get_instances():
                    v=i.get_reading_for_attribute(a).get_most_probable().get_name()
                    border_search_list.append([v])
                border_search_df = pd.DataFrame(border_search_list,columns=['values'])
                border_search_df['values']=border_search_df['values'].astype('f8')
                border_search_df['class'] = cl
                border_search_df=border_search_df.sort_values(by='values')
                border_search_df['values_shift']=border_search_df['values'].shift(1)
                border_search_df['class_shitf'] = border_search_df['class'].shift(1)
                border_search_shift = border_search_df[border_search_df['class_shitf'] != border_search_df['class']]
                values = np.unique((border_search_shift['values']+border_search_shift['values_shift']).dropna()/2).astype('str') # take the middle value 
                
                #divide into j_jobs batches
                if n_jobs is not None:
                    if n_jobs == -1:
                        n_jobs = cpu_count()
                    values_batches = np.array_split(values, n_jobs)
                    with Pool() as pool:
                        results = pool.starmap(self.calculate_split_criterion, [(v, data, a, stats, entropy, entropyEvaluator, self.min_impurity_decrease,beta) for v in values_batches])
                        temp_gain = 0
                        for best_split_candidate_c, value_to_split_on_c, temp_gain_c, pure_temp_gain_c in results:
                            if temp_gain_c > temp_gain:
                                best_split_candidate=best_split_candidate_c 
                                value_to_split_on =value_to_split_on_c
                                temp_gain =temp_gain_c
                                pure_temp_gain=pure_temp_gain_c
                else:
                    best_split_candidate, value_to_split_on, temp_gain, pure_temp_gain = self.calculate_split_criterion(values=values, 
                                                                                                                        data=data, 
                                                                                                                        attribute=a, 
                                                                                                                        stats=stats, 
                                                                                                                        globalEntropy=entropy, 
                                                                                                                        entropyEvaluator=entropyEvaluator, 
                                                                                                                        min_impurity_decrease=self.min_impurity_decrease,
                                                                                                                        beta=beta)
                    

            #this was move out from the loop to reduce numerical errors while iteratively sum and divide
            if a.get_type() == Attribute.TYPE_NOMINAL:
                conf_for_value = stats.get_avg_confidence()
                pure_temp_gain=entropy-temp_gain
                temp_gain = conf_for_value*pure_temp_gain
            if temp_gain >= info_gain and (pure_temp_gain/entropy)>=self.min_impurity_decrease:
                info_gain = temp_gain
                pure_info_gain=pure_temp_gain
                best_split = best_split_candidate
                best_split_candidate.set_importance_gain(pure_info_gain)
                best_split_candidate.set_value_to_split_on(value_to_split_on)
                
        # if nothing better can happen
        if best_split == None:
            # create the only node and summary for it
            class_att = data.get_class_attribute()
            root = TreeNode(class_att.get_name(), data.calculate_statistics(class_att))
            root.set_type(class_att.get_type())
            tree = Tree(root)
            if depth == 0:
                self.tree = tree
            return tree
        # Create root node, and recursively go deeper into the tree.
        class_att = data.get_class_attribute()
        class_stats = data.calculate_statistics(class_att)
        root = TreeNode(best_split.get_name(), class_stats)
        root.set_type(class_att.get_type())

        # attach newly created trees
        for val in best_split.get_splittable_domain():
            if best_split.get_type() == Attribute.TYPE_NOMINAL:
                best_split_stats = data.calculate_statistics(best_split)
                new_data = data.filter_nominal_attribute_value(best_split, val)
                subtree = self.fit(new_data, entropyEvaluator=entropyEvaluator, depth=depth + 1)
                if subtree and best_split_stats.get_most_probable().get_confidence() > self.GROW_CONFIDENCE_THRESHOLD:
                    root.add_edge(TreeEdge(Value(val, best_split_stats.get_avg_confidence()), subtree.get_root()))
                    root.set_infogain(best_split.get_importance_gain())

            elif best_split.get_type() == Attribute.TYPE_NUMERICAL:
                best_split_stats = data.calculate_statistics(best_split)
                new_data_less_then,new_data_greater_equal = data.filter_numeric_attribute_value(best_split, val)
                if len(new_data_less_then) >= self.node_size_limit and len(new_data_greater_equal) >= self.node_size_limit:
                    subtree_less_than = self.fit(new_data_less_then, entropyEvaluator=entropyEvaluator, depth=depth + 1)
                    subtree_greater_equal = self.fit(new_data_greater_equal, entropyEvaluator=entropyEvaluator, depth=depth + 1)
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
    def calculate_split_criterion( values, data, attribute, stats, globalEntropy, entropyEvaluator,min_impurity_decrease, beta=1):
        temp_gain = 0
        temp_numeric_gain = 0
        pure_temp_gain=0
        local_info_gain = 0
        value_to_split_on = None
        for v in values:  
            subdata = None
            subdataLessThan = None
            subdataGreaterEqual = None
            if attribute.get_type() == Attribute.TYPE_NOMINAL:
                subdata = data.filter_nominal_attribute_value(attribute, v)
            elif attribute.get_type() == Attribute.TYPE_NUMERICAL:
                subdata_less_than,subdata_greater_equal = data.filter_numeric_attribute_value(attribute, v)
            if attribute.get_type() == Attribute.TYPE_NOMINAL:
                stat_for_value = len(subdata)/len(data)
                temp_gain += (stat_for_value) * entropyEvaluator.calculate_entropy(subdata)
            elif attribute.get_type() == Attribute.TYPE_NUMERICAL:
                stat_for_lt_value = len(subdata_less_than)/len(data)
                stat_for_gte_value = len(subdata_greater_equal)/len(data)
                conf_for_value = stats.get_avg_confidence()
                pure_single_temp_gain = (globalEntropy - (stat_for_lt_value*entropyEvaluator.calculate_entropy(subdata_less_than)+
                                                                                       (stat_for_gte_value)*entropyEvaluator.calculate_entropy(subdata_greater_equal)))
                rescaled_conf = conf_for_value*globalEntropy
                if pure_single_temp_gain*rescaled_conf == 0:
                    #to prevent from 0-division
                    single_temp_gain=0
                else:
                    single_temp_gain = ((1+beta**2)*rescaled_conf*pure_single_temp_gain)/((beta**2*rescaled_conf)+pure_single_temp_gain)
                if single_temp_gain >= temp_numeric_gain:
                    temp_numeric_gain = single_temp_gain
                    temp_gain = single_temp_gain
                    pure_temp_gain= pure_single_temp_gain
                    value_to_split_on = v
                    
        if attribute.get_type() == Attribute.TYPE_NOMINAL:
            conf_for_value = stats.get_avg_confidence()
            pure_temp_gain=globalEntropy-temp_gain
            temp_gain = conf_for_value*pure_temp_gain
        if temp_gain >= local_info_gain and (pure_temp_gain/globalEntropy)>=min_impurity_decrease:
            best_split = attribute
            
        return best_split, value_to_split_on, temp_gain, pure_temp_gain

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