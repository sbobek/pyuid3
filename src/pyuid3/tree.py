# AUTOGENERATED! DO NOT EDIT! File to edit: src/tree.ipynb (unless otherwise specified).

__all__ = ['Tree']

# Cell
from .tree_node import TreeNode
from .value import Value
from .att_stats import AttStats
from .instance import Instance
from .attribute import Attribute

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
                if te.get_value().get_name() == most_probable.get_name():
                    new_node = te.getChild()
                    break

            if new_node:
                test_node = new_node
            else:
                break

        return test_node.get_stats()

    def error(self, i: Instance) -> bool:
        result = self.predict(i)

        return result.get_most_porbable().get_name() == i.get_readings().get_last().get_most_probable().get_name()

    def get_attributes(self) -> set:
        return self.fill_attributes(set(), self.root)

    def to_HML(self) -> str:
        result = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<hml version=\"2.0\">"


        #types are defined by atts domains
        atts = get_attributes()
        result += "<types>\n"
        for att in atts:
            result += f"<type id=\"tpe_{att.get_name()}\" name=\"{att.get_name()}\" base=\"symbolic\">\n"
            result += "<domain>\n"
            for v in att.get_domain():
                result += f"<value is=\"{v}\"/>\n"

            result += "</domain>\n"
            result += "</type>\n"

        result += "</types>\n"
        #attributes

        result += "<attributes>\n"
        for att in atts:
            result += f"<attr id=\"{att.get_name()}\" type=\"tpe_{att.get_name()}\" name=\"{att.get_name()}\" clb=\" \" abbrev=\"{att.get_name()}\" class=\"simple\" comm=\"io\"/>\n"

        result += "</attributes>\n"

        #tables and rules
        result +="<xtt>\n"

        result += f"<table id=\"id_{self.get_class_attribute().get_name()}\" name=\"{self.get_class_attribute().get_name()}\">"
        result += "<schm><precondition>"
        for att in atts:
            if not att == self.get_class_attribute():
                result += f"<attref ref=\"{att.get_name()}\"/>\n"

        result += "</precondition><conclusion>\n"
        result += f"<attref ref=\"{self.get_class_attribute().get_name()}\"/>\n"
        result += "</conclusion>\n</schm>\n"

        #rules

        rules = get_rules()

        decision_att = self.get_class_attribute().get_name()
        dec_att = self.get_class_attribute()
        cond_atts_list = list(atts)
        cond_atts_list.remove(dec_att)

        for rule in rules:
            result += "<rule id=\"rule_"+hash(rule)+"\">\n" + "<condition>\n"

            #conditions
            for att in atts:
                value = Value("any",1.0)
                for c in rule:
                    if c.att_name == att.get_name():
                        value = c.value

                result += "<relation name=\"eq\">\n"
                result +=  f"<attref ref=\"{att.get_name()}\"/>\n<set>  <value is=\"{value.get_name()}\"/>\n</set> </relation>"


            result += "</condition>\n"
            result += "<decision>\n"
            #decision

            confidence = 1
            for c in rule:
                confidence *= c.value.get_confidence()

            for c in rule:
                if c.att_name == decision_att:
                    result += f"<trans>\n<attref ref=\"{c.att_name}\"/>\n"
                    result += "<set>"
                    result += f"<value is=\"{c.value.get_name()}(#{round((confidence*2-1)*100.0)/100.0})\"/>\n"
                    result += "</set></trans>\n"

            result += "</decision>\n"
            result += "</rule>\n"

        result += "</table></xtt><callbacks/></hml>\n"

        return result

    def save_HML(self, filename: str) -> None:
        f = open(f"{filename}.txt", "w")
        f.write(self.to_HML())
        f.close()

    def get_importances(self) -> str:
        imps = []
        atts = self.get_attributes()
        for a in atts:
            if a.get_name() == self.get_class_attribute().get_name():
                break
            imps.append(str(a.get_importance_gain()))

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

                result +=  f"{att.get_name()} {value.get_name().replace('>=',' gte ').replace('<',' lt ')},"

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

    def save_dot(self, filename: str) -> None:
        f = open(f"{filename}.txt", "w")
        f.write(self.to_dot())
        f.close()

    def get_class_attribute(self) -> Attribute:
        temp  = self.root
        while not temp.is_leaf():
            temp = temp.get_edges()[0].get_child()

        result = Attribute(temp.get_att(), set())
        for v in temp.get_stats().het_statistics():
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
                for v in root.get_stats().het_statistics():
                    att.add_value(v.get_name())

                result.add(att)

            return result
         else:

            return self.fill_attributes(set(), root)

    def to_dot(self, parent=None) -> str:
        if parent:
            result = ""
            label = parent.get_att() + "\n"
            if parent.is_leaf():
                # Add classification info to leaves
                for v in parent.get_stats().het_statistics():
                    label += str(v) + "\n"

            col = "red" if parent.is_leaf() else "black"
            result += f"{hash(parent)}[label=\" {label} \",shape=box, color={col}]"

            for te in parent.get_edges():
                result += f"{hash(parent)}->{hash(te.get_child())}[label=\"{te.get_value().get_name()}\n conf={round(te.get_value().get_confidence() * 100.0) / 100.0} \"]\n"
                result += self.to_dot(te.get_child())

            return result

        else:
            result = "digraph mediationTree{\n"
            result += self.to_dot(self.root)

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