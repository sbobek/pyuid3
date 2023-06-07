# AUTOGENERATED! DO NOT EDIT! File to edit: src/tree.ipynb (unless otherwise specified).

__all__ = ['Tree']

# Cell
from .tree_node import TreeNode
from .value import Value
from .att_stats import AttStats
from .instance import Instance
from .attribute import Attribute
from collections import defaultdict
import re
import pandas as pd
import os
import seaborn as sns
from matplotlib import pyplot as plt

# Cell
class Tree:
    def __init__(self, root: TreeNode):
        self.root = root

    def get_root(self) -> TreeNode:
        return self.root

    def predict(self, i: Instance) -> AttStats:
        test_node = self.get_root()
        while not test_node.is_leaf():
            att_to_test = test_node.get_att()
            r = i.get_reading_for_attribute(att_to_test)
            most_probable = r.get_most_probable()

            new_node = None
            for te in test_node.get_edges():
                if test_node.get_type() == Attribute.TYPE_NOMINAL:
                    if te.get_value().get_name() == most_probable.get_name():
                        new_node = te.get_child()
                        break
                elif test_node.get_type() == Attribute.TYPE_NUMERICAL:
                    tev = te.get_value().compile_expr(i)#.get_name()                    
                    if eval(f'{most_probable.get_name()}{tev}'):
                        new_node = te.get_child()
                        break

            if new_node:
                test_node = new_node
            else:
                break

        return test_node.get_stats()
    
    def justification_tree(self, i: Instance) -> str:
        test_node = self.get_root()
        root_handle=test_node.copy()
        root_handle.set_edges([])
        temp_root = root_handle
        while not test_node.is_leaf():
            att_to_test = test_node.get_att()
            r = i.get_reading_for_attribute(att_to_test)
            most_probable = r.get_most_probable()

            new_node = None
            for te in test_node.get_edges():
                if test_node.get_type() == Attribute.TYPE_NOMINAL:
                    if te.get_value().get_name() == most_probable.get_name():
                        new_node = te.get_child()
                        te_copy = te.copy()
                        temp_root.set_edges([te_copy])
                        temp_root = te_copy.get_child()
                        break
                elif test_node.get_type() == Attribute.TYPE_NUMERICAL:
                    tev = te.get_value().compile_expr(i)#.get_name()                    
                    if eval(f'{most_probable.get_name()}{tev}'):
                        new_node = te.get_child()
                        te_copy = te.copy()
                        temp_root.set_edges([te_copy])
                        temp_root = te_copy.get_child()
                        break
                

            if new_node:
                test_node = new_node
            else:
                break

        return Tree(root=root_handle)

    def error(self, i: Instance) -> bool:
        result = self.predict(i)

        return result.get_most_porbable().get_name() == i.get_readings().get_last().get_most_probable().get_name()

    def get_attributes(self) -> set:
        return self.fill_attributes(set(), self.root)

    def get_importances(self) -> str:
        imps = []
        atts = self.get_attributes()
        for a in atts:
            if a.get_name() == self.get_class_attribute().get_name():
                break
            imps.append(str(a.get_importance_gain()))
            print(a, a.get_importance_gain(), "============================")

        return ','.join(imps)

    def to_HMR(self) -> str:
        result = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% TYPES DEFINITIONS %%%%%%%%%%%%%%%%%%%%%%%%%%\n\n"

        #types are defined by atts domains
        atts = self.get_attributes()
        for att in atts:
            result += f"xtype [\n name: {att.get_name()}, \n"
            if att.get_type() == Attribute.TYPE_NOMINAL:
                result += f"base:symbolic,\n domain : ["
                domain_res = ""
                for v in att.get_domain():
                    domain_res += f"{v},"

                result += domain_res.strip()[:-1].replace("[<>=]","")

            elif att.get_type() == Attribute.TYPE_NUMERICAL:
                result += "base:numeric,\n" + "domain : ["
                result += "-100000 to 100000"

            result += "]].\n"

        result += "\n%%%%%%%%%%%%%%%%%%%%%%%%% ATTRIBUTES DEFINITIONS %%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        for att in atts:
            result += f"xattr [ name: {att.get_name()},\n type:{att.get_name()},\n class:simple,\n comm:out ].\n"

        #tables and rules
        result +="\n%%%%%%%%%%%%%%%%%%%%%%%% TABLE SCHEMAS DEFINITIONS %%%%%%%%%%%%%%%%%%%%%%%%\n"

        result += " xschm tree : ["
        for att in atts:
            if not att == self.get_class_attribute():
                result += f"{att.get_name()},"

        result = f"{result.strip()[:-1]}]"
        result += f"==> [{self.get_class_attribute().get_name()}].\n"

        #rules

        rules = self.get_rules()
        decision_att = self.get_class_attribute().get_name()
        dec_att = self.get_class_attribute()
        cond_atts = Attribute()
        cond_atts_list = list(atts)
        cond_atts_list.remove(dec_att)

        for i, rule in enumerate(rules):
            result += f"xrule tree/{i}:\n["

            #conditions
            for att in atts:
                if att.get_name() == self.get_class_attribute().get_name():
                    continue

                value = Value("any", 1.0)

                for c in rule:
                    if c.att_name == att.get_name():
                        value = c.value
                        result +=  f"{att.get_name()} {value.get_name().replace('>=',' gte ').replace('<',' lt ')}, "

            result = f"{result.strip()[:-1]}] ==> ["

            #decision

            confidence = 1
            for c in rule:
                confidence *= c.value.get_confidence()

            for c in rule:
                if c.att_name == decision_att:
                    ex = '\\['
                    result += f"{decision_att} set {c.value.get_name().split(ex)[0]}"

            confidence = confidence * 10 / 10.0
            result += f"]. # {confidence}\n"


        # result += "</table></xtt><callbacks/></hml>\n"
        return result
    
    def to_pseudocode(self, reduce=True, operators_mapping=None) -> str:
        result = ""
        if operators_mapping is None:
            operators_mapping = {'if':'IF',
                                 'then':'THEN',
                                 'and':'AND',
                                 'eq':'==',
                                 '<':'<', 
                                 '>=':'>=',
                                 'set':'='
                                }
            

        decision_att = self.get_class_attribute().get_name()
        list_result = self.to_dict(reduce=reduce, operators_mapping=operators_mapping)
        result = ""
        for rule in list_result:
            result+=operators_mapping['if']+" "
            conditional_part=[]
            for k,v in rule['rule'].items():
                conditional_part.append(f'{k} '+f" {operators_mapping['and']} {k} ".join(v))
            result+=f" {operators_mapping['and']} ".join(conditional_part)
            ex = '\\['
            result += f" {operators_mapping['then']} {decision_att} {operators_mapping['set']} {rule['prediction']}"
            result += f" # {rule['confidence']}\n"

        return result

    def to_dict(self, reduce = True, operators_mapping=None) -> str:
        result = []
        if operators_mapping is None:
            operators_mapping = {'if':'IF',
                                 'then':'THEN',
                                 'and':'AND',
                                 'eq':'==',
                                 '<':'<', 
                                 '>=':'>=',
                                 'set':'='
                                }
            

        #types are defined by atts domains
        atts = self.get_attributes()
        rules = self.get_rules()
        decision_att = self.get_class_attribute().get_name()
        dec_att = self.get_class_attribute()
        cond_atts = Attribute()
        cond_atts_list = list(atts)
        cond_atts_list.remove(dec_att)

        for i, rule in enumerate(rules):
            conditions = []
            condition_values=[]
            #conditions
            for att in atts:
                if att.get_name() == self.get_class_attribute().get_name():
                    continue

                value = Value("any", 1.0)

                for c in rule:
                    if c.att_name == att.get_name():
                        value = c.value
                        if att.get_type() == Attribute.TYPE_NOMINAL:
                            condition_value = f"{operators_mapping['eq']} {value.get_name()}"
                        else:
                            condition_value = value.get_name().replace('>=',f"{operators_mapping['>=']} ").replace('<',f"{operators_mapping['<']} ")
                        
                        condition_values.append(condition_value)
                        conditions.append(f"{att.get_name()}".strip())

            #decision

            confidence = 1
            for c in rule:
                confidence *= c.value.get_confidence()

            for c in rule:
                if c.att_name == decision_att:
                    ex = '\\['
                    prediction = c.value.get_name().split(ex)[0]

            confidence = confidence * 10 / 10.0

            rule_dict_long = defaultdict(list)
            for k, v in zip(conditions, condition_values):
                rule_dict_long[k].append(v)
            
            if reduce: 
                rule_dict = {}
                for k,v in rule_dict_long.items():
                    rule_dict[k] = self.__reduce_condition(rule_dict_long[k], operators_mapping=operators_mapping)
            else:
                rule_dict = dict(rule_dict_long)
            
            result.append(dict({'rule':rule_dict, 'prediction':prediction, 'confidence':confidence}))


        return result
    
    def __reduce_condition(self, conditions: list, operators_mapping: dict) -> list:
        #only for numerical and non-linear split
        result = []
        lt = [c for c in conditions if operators_mapping['<'] in c]
        if len(lt) > 0:
            to_minimize = [float(re.sub(operators_mapping['<'],'',x)) for x in lt if  not re.search(r'\b[a-zA-Z_]\w*\b',x)]
            if len(to_minimize) > 0:
                lt_condition = min(to_minimize)
                result.append(f"{operators_mapping['<']}{lt_condition}")
            for lcd in [re.sub(operators_mapping['<'],'',x) for x in lt if  re.search(r'\b[a-zA-Z_]\w*\b',x)]:
                result.append(f"{operators_mapping['<']}{lcd}")

        gte = [c for c in conditions if operators_mapping['>='] in c]
        if len(gte) > 0:
            to_maximize = [float(re.sub(operators_mapping['>='],'',x)) for x in gte if  not re.search(r'\b[a-zA-Z_]\w*\b',x)]
            if len(to_maximize)>0:
                gte_condition = max(to_maximize)
                result.append(f"{operators_mapping['>=']}{gte_condition}")
            for gcd in [re.sub(operators_mapping['>='],'',x) for x in gte if  re.search(r'\b[a-zA-Z_]\w*\b',x)]:
                result.append(f"{operators_mapping['>=']}{gcd}")
        return result+[c for c in conditions if operators_mapping['eq'] in c]
    
    def save_dot(self, filename: str, fmt=None,  visual=False, background_data:pd.DataFrame=None, 
                instance2explain=None, counterfactual=None) -> None:
        f = open(filename, "w")
        if visual:
            if background_data is not None:
                if instance2explain is not None and not isinstance(instance2explain, pd.DataFrame):
                    counterfactual=pd.DataFrame(instance2explain)
                if counterfactual is not None and not isinstance(counterfactual, pd.DataFrame):
                    counterfactual=pd.DataFrame(counterfactual)
            f.write(self.to_dot_visual(parent=None, fmt=fmt, background_data=background_data,
                                      instance2explain=instance2explain, counterfactual=counterfactual))
        else:
            f.write(self.to_dot(parent=None,fmt=fmt))
        f.close()

    def get_class_attribute(self) -> Attribute:
        temp  = self.root
        while not temp.is_leaf():
            temp = temp.get_edges()[0].get_child()

        result = Attribute(temp.get_att(), set())
        for v in temp.get_stats().get_statistics():
            result.add_value(v.get_name())

        return result

    def fill_rules(self, rules: list, current_rule: list, root: TreeNode) -> list:
        if not current_rule:
            current_rule = []

        att_name = root.get_att()
        if not root.is_leaf():
            for e in root.get_edges():
                new_rule = current_rule.copy()
                new_rule.append(self.Condition(att_name, e.get_value(), "eq"))
                self.fill_rules(rules, new_rule, e.get_child())

        else:
            final_rule = current_rule.copy()
            final_rule.append(self.Condition(att_name, root.get_stats().get_most_probable(), "set"))
            rules.append(final_rule)

        return rules

    def get_rules(self) -> list:
        return self.fill_rules([], None, self.get_root())

    def fill_attributes(self, result=None, root=None) -> set:
         if result != None and root!= None:
            att_name = root.get_att()
            att = Attribute(att_name, set(), root.get_type())
            att.set_importance_gain(root.get_infogain())
            if att in result:
                for tmp in result:
                    if tmp == att:
                        att = tmp
                        break

            if not root.is_leaf():
                for  e in root.get_edges():
                    att.add_value(e.get_value().get_name())
                    self.fill_attributes(result, e.get_child())

                result.add(att)
            else:
                for v in root.get_stats().get_statistics():
                    att.add_value(v.get_name())

                result.add(att)

            return result
         else:

            return self.fill_attributes(set(), root)

    def to_dot(self, parent=None, fmt=None) -> str:
        if parent:
            result = ""
            label = parent.get_att() + "\n"
            if parent.is_leaf():
                # Add classification info to leaves
                for v in parent.get_stats().get_statistics():
                    label += str(v) + "\n"

            col = "red" if parent.is_leaf() else "black"
            result += f"{hash(parent)}[label=\" {label} \",shape=box, color={col}]"

            for te in parent.get_edges():
                if parent.get_type() == Attribute.TYPE_NUMERICAL and fmt is not None:
                    value = te.get_value().get_name()
                    value=self.__format_expression(value,fmt)
                else:
                    value = value=te.get_value().get_name()
                result += f"{hash(parent)}->{hash(te.get_child())}[label=\"{value}\n conf={round(te.get_value().get_confidence() * 100.0) / 100.0} \"]\n"
                result += self.to_dot(te.get_child(),fmt=fmt)

            return result

        else:
            result = "digraph mediationTree{\n"
            result += self.to_dot(self.root,fmt=fmt)

            return result+"\n}"
        
    @staticmethod    
    def __find_features(background_data, expr):
        features = sorted(background_data.columns,key=len,reverse=True)
        columns=[]
        for f in features:
            if f in expr:
                expr = expr.replace(f, "")
                columns+=[f]
        return columns
    
    def __format_expression(self,value,fmt):
        value_tr = value
        for f in [a.get_name() for a in self.get_attributes()]:
            value_tr = re.sub(r'\b[a-zA-Z_]\w*\b','',value_tr)
        numbers = re.findall("[-]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", value_tr)
        formatted = [("{value:"+fmt+"}").format(value=float(v)) for v in numbers]
        for k,v in zip(numbers, formatted):
            value = value.replace(k,v)
        return value

    def to_dot_visual(self, parent=None, background_data: pd.DataFrame=None, instance2explain=None, counterfactual=None, file_format='png', palette='Set2', fmt=None) -> str:
        path = '.'
        features=[]
        target_column = background_data.columns[-1]
        if not os.path.exists(path+'/imgs/'):
            os.makedirs(path+'/imgs/')
        if parent:
            result = ""
            col = "red" if parent.is_leaf() else "black"
            if parent.is_leaf():
                fig,ax=plt.subplots(figsize=(3,3))
                if instance2explain is not None:
                    background_data = pd.concat((instance2explain,background_data))
                if counterfactual is not None:
                    background_data = pd.concat((counterfactual,background_data))
                stats = background_data[[target_column]].value_counts().to_frame('samples').sort_index().reset_index()
                sns.barplot(data = stats,
                            x=target_column,y='samples', alpha=0.7,palette=palette,ax=ax)

                if instance2explain is not None:
                    pos = stats[stats[target_column]==instance2explain[target_column].values[0]].index[0]
                    ax.plot(pos,1, 'or', markersize=8)
                if counterfactual is not None:
                    pos = stats[stats[target_column]==counterfactual[target_column].values[0]].index[0]
                    ax.plot(pos,1, 'ob', markersize=8)
                ax.bar_label(ax.containers[-1], labels=[f'{l:.2f}%' for l in list(background_data[[target_column]].value_counts(normalize=True).sort_index()*100)], label_type='center')
                plt.savefig(f'{path}/imgs/{hash(parent)}.{file_format}', format=file_format,bbox_inches='tight')
                plt.close()
                result += f"{hash(parent)}[label=\"\",shape=box, color={col},image=\"{path}/imgs/{hash(parent)}.{file_format}\"]"

            has_plotted=False
            for te in parent.get_edges():

                sibling_data = background_data.query(parent.get_att()+' '+te.get_value().get_name())
                                                     
                if not has_plotted and not parent.is_leaf():
                    result += f"{hash(parent)}[label=\"\",shape=box, color={col}, image=\"{path}/imgs/{hash(parent)}.{file_format}\"]"
                    has_plotted = True
                    if re.search('[a-zA-Z_]',te.get_value().get_name()):
                        #it's and expression, and we need to visualize it as a plot of two features
                        plt.figure(figsize=(8,3))
                        features = Tree.__find_features(background_data,te.get_value().get_name())
                        grid=sns.scatterplot(data = background_data[features+[parent.get_att(),target_column]], x=features[0],y=parent.get_att(),
                                        hue=target_column,palette=palette,alpha=0.5)
                        if instance2explain is not None:
                            ax = grid.axes
                            ax.plot(instance2explain[features[0]],instance2explain[parent.get_att()], 'or', markersize=8)
                        if counterfactual is not None:
                            ax = grid.axes
                            ax.plot(counterfactual[features[0]],counterfactual[parent.get_att()], 'ob', markersize=8)
                        grid.axes.set_title(f"{parent.get_att()}",fontsize=20)
                        data = background_data.eval(re.sub("[<>=]","",te.get_value().get_name())).to_frame(parent.get_att())
                        data[features[0]] = background_data[features[0]]
                        sns.lineplot(data=data,x=features[0],y=parent.get_att(), linestyle='--',color='r')
                        plt.savefig(f'{path}/imgs/{hash(parent)}.{file_format}', format=file_format,bbox_inches='tight')
                        plt.close()
                    else:
                        grid=sns.displot(background_data, x=parent.get_att(),hue=target_column,kind='hist',fill=True,height=3,
                                         palette=palette,aspect=3,alpha=0.5)
                        ax = grid.axes[0][0]
                        ax.set_title(f"{parent.get_att()}",fontsize=20)
                        ax.axvline(float(re.sub("[<>=]","",te.get_value().get_name())),linestyle='--',color='r')
                        if instance2explain is not None:
                            ax.plot(instance2explain[parent.get_att()],1, 'or', markersize=8)
                        if counterfactual is not None:
                            ax.plot(counterfactual[parent.get_att()],1, 'ob', markersize=8)
                        plt.savefig(f'{path}/imgs/{hash(parent)}.{file_format}', format=file_format,bbox_inches='tight')
                        plt.close()
                if parent.get_type() == Attribute.TYPE_NUMERICAL and fmt is not None:
                    value = te.get_value().get_name()
                    value=self.__format_expression(value,fmt)
                else:
                    value = value=te.get_value().get_name()
                    
                result += f"{hash(parent)}->{hash(te.get_child())}[label=\"{value}\n conf={round(te.get_value().get_confidence() * 100.0) / 100.0} \"]\n"
                sibling_instance2explain=instance2explain
                sibling_counterfactual=counterfactual
                if instance2explain is not None:
                    if len(instance2explain.query(parent.get_att()+' '+te.get_value().get_name())) == 0:
                        sibling_instance2explain=None 
                if counterfactual is not None:
                    if len(counterfactual.query(parent.get_att()+' '+te.get_value().get_name())) == 0:
                        sibling_counterfactual=None 
                result += self.to_dot_visual(parent=te.get_child(),background_data=sibling_data,
                                            instance2explain=sibling_instance2explain, 
                                            counterfactual=sibling_counterfactual,palette=palette,fmt=fmt)

            return result

        else:

            palette = dict(zip(background_data[target_column].unique(),sns.color_palette(palette,background_data[target_column].nunique())))

            result = "digraph mediationTree{\n"
            result += self.to_dot_visual(parent=self.root, background_data=background_data,instance2explain=instance2explain, counterfactual=counterfactual, palette=palette,fmt=fmt)

            return result+"\n}"


    def __str__(self, lvl=None, val=None, node=None):
        if lvl != None and val and node:
            result = "|"
            res = "-------" * lvl
            result = result + res
            result += f"is  {val}"
            if node.is_leaf():
                result += f" then {node.get_att()} = {node.get_stats()} \n"
            else:
                result += f"then if {node.get_att()} (play= {node.get_stats()} )\n"
            lvl += 1
            for te in node.get_edges():
                result += self.__str__(lvl, te.get_value(),te.get_child())
        else:
            result = f"if {self.root.get_att()} (play= {self.root.get_stats()})\n"
            for te in self.root.get_edges():
                result += self.__str__(0, te.get_value(), te.get_child())

        return result



    class Condition:
        def __init__(self, att_name: str, value: Value, op='eq'):
            self.att_name = att_name
            self.value = value
            self.op = op