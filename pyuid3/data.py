# AUTOGENERATED! DO NOT EDIT! File to edit: src/data.ipynb (unless otherwise specified).

__all__ = ['Data']

# Cell
from io import TextIOWrapper, StringIO
import traceback
import re
import pandas as pd
from pandas import DataFrame
from typing import List, Set
from typing import Tuple
from collections import OrderedDict

from .reading import Reading
from .instance import Instance
from .att_stats import AttStats
from .attribute import Attribute

# Cell
class Data:
    REAL_DOMAIN = '@REAL'

    def __init__(self, name: str = None, attributes: List[Attribute] = None, instances: List[Instance] = None):
        self.name = name
        self.instances = instances
        self.attributes = OrderedDict()
        for at in attributes:
            self.attributes[at.get_name()]=at
            
        if len(attributes) > 0:
            self.class_attribute_name = attributes[-1].get_name()
        else:
            self.class_attribute_name = None
        
    def __len__(self):
        return len(self.instances)

    def filter_nominal_attribute_value(self, at: Attribute, value: str) -> 'Data':
        new_instances = []
        new_attributes = self.get_attributes().copy()

        for i in self.instances:
            reading = i.get_reading_for_attribute(at.get_name())
            instance_val = reading.get_most_probable().get_name()
            if str(instance_val) == str(value):
                new_readings = i.get_readings().copy()
                new_instances.append(Instance(new_readings))

        return Data(self.name, new_attributes, new_instances)

    def filter_numeric_attribute_value(self, at: Attribute, value: str) -> Tuple['Data','Data']:
        new_instances_less_than = []
        new_instances_greater_equal = []
        new_attributes_lt = self.get_attributes().copy()
        new_attributes_gt = self.get_attributes().copy()
        value = float(value)
        for i in self.instances:
            reading = i.get_reading_for_attribute(at.get_name())
            instance_val = reading.get_most_probable().get_name()
            if float(instance_val) < value:
                new_readings = i.get_readings().copy()
                new_instances_less_than.append(Instance(new_readings))
            elif float(instance_val) >= value:
                new_readings = i.get_readings().copy()
                new_instances_greater_equal.append(Instance(new_readings))

        return (Data(self.name, new_attributes_lt, new_instances_less_than),Data(self.name, new_attributes_gt, new_instances_greater_equal))

    def get_attribute_of_name(self, att_name: str) -> Attribute:
        if at.get_name() in self.attributes.keys():
            return self.attributes[at.get_name()]
        else:
            return None

    def to_arff_most_probable(self) -> str:
        result = '@relation ' + self.name + '\n'
        for at in self.attributes:
            result += at.to_arff() + '\n'

        result += '@data\n'

        for i in self.instances:
            for r in i.get_readings():
                result += r.get_most_probable().get_name()
                result += ','
            result = result[:-1]  # delete the last coma ','
            result += '\n'
        return result

    def to_arff_skip_instance(self, epsilon: float) -> str:
        result = '@relation ' + self.name + '\n'
        for at in self.attributes:
            result += at.to_arff() + '\n'

        result += '@data\n'

        for i in self.instances:
            partial = ''
            for r in i.get_readings():
                if r.get_most_probable().get_confidence() > epsilon:
                    partial += r.get_most_probable().get_name()
                else:
                    break
                partial += ','
            result = result[:-1]  # delete the last coma ','
            result += partial + '\n'

        return result

    def to_arff_skip_value(self, epsilon: float) -> str:
        result = '@relation ' + self.name + '\n'
        for at in self.attributes:
            result += at.to_arff() + '\n'

        result += '@data\n'

        for i in self.instances:
            partial = ''
            for r in i.get_readings():
                if r.get_most_probable().get_confidence() > epsilon:
                    partial += r.get_most_probable().get_name()
                else:
                    partial += '?'
                partial += ','
            result = result[:-1]  # delete the last coma ','
            result += partial + '\n'

        return result

    def to_uarff(self) -> str:
        result = '@relation ' + self.name + '\n'
        for at in self.attributes:
            result += at.to_arff() + '\n'

        result += '@data\n'

        for i in self.instances:
            result += i.to_arff() + '\n'

        return result

    def calculate_statistics(self, att: Attribute) -> AttStats:
        return AttStats.calculate_statistics(att, self)

    @staticmethod
    def __read_uarff_from_buffer(br: (TextIOWrapper, StringIO)) -> 'Data':
        atts = []
        insts = []
        name = br.readline().split('@relation')[1].strip()
        for line in br:
            if len(line) == 1:
                continue
            att_split = line.strip().split('@attribute')
            if len(att_split) > 1:
                att = Data.parse_attribute(att_split[1].strip())
                atts.append(att)
            elif line.strip() == '@data':
                break

        # read instances
        for line in br:
            inst = Data.parse_instances(atts, line.strip())
            insts.append(inst)

        tmp_data = Data(name, atts, insts)
        tmp_data.update_attribute_domains()
        return tmp_data

    @staticmethod
    def __read_ucsv_from_dataframe(df: DataFrame, name: str) -> 'Data':
        atts = []
        insts = []
        cols = list(df.columns)
        for col in cols:
            records = set(df[col])
            records = set(re.sub(r'\[[0-9.]*]', '', str(rec)) for rec in records)
            records = list(records)
            if len(records) == 1:
                records = records[0].split(';')
            if len(records) > 10:
                att = col + ' @REAL'  # mark as a real value
            else:
                att = str(records).strip("'").strip('[').strip(']')
                att = col + ' {' + att + '}'
            att = Data.parse_attribute(att)
            atts.append(att)

        br = StringIO(df.to_string(index=False))
        br.readline()
        for line in br:
            line = re.sub(' +', ',', line.strip())
            inst = Data.parse_instances(atts, line)
            insts.append(inst)

        tmp_data = Data(name, atts, insts)
        tmp_data.update_attribute_domains()
        return tmp_data

    def update_attribute_domains(self):
        for a in self.get_attributes():
            if a.get_type() == Attribute.TYPE_NUMERICAL:
                domain = self.__get_domain_from_data(a, self.instances)
                a.set_domain(domain)

    def __get_domain_from_data(self, a: Attribute, instances: List[Instance]) -> Set[str]:
        domain = set()
        for i in instances:
            value = i.get_reading_for_attribute(a.get_name()).get_most_probable().get_name()
            domain.add(value)
        return domain

    @staticmethod
    def parse_ucsv(filename: str) -> 'Data':
        df = pd.read_csv(filename)
        name = filename.split('/')[-1].split('.csv')[0]
        out = Data.__read_ucsv_from_dataframe(df, name)
        return out
    
    @staticmethod
    def parse_dataframe(df: pd.DataFrame,name='uarff_data') -> 'Data':
        out = Data.__read_ucsv_from_dataframe(df, name)
        return out

    @staticmethod
    def __parse(temp_data: 'Data', class_id: (int, str)) -> 'Data':
        # if class name is given
        if isinstance(class_id, str):
            class_att_name = class_id
            class_att = temp_data.get_attribute_of_name(class_att_name)
        elif isinstance(class_id, int):
            class_att_name = list(temp_data.attributes.keys())[class_id]
            class_att = temp_data.attributes[class_att]

        del temp_data.attributes[class_att_name]
        temp_data.attributes.append((class_att_name,class_att))
        # change order of reading for the att
        for i in temp_data.instances:
            class_label = i.get_reading_for_attribute(class_att.get_name())
            readings = i.get_readings()
            del readings[class_index]
            readings.append(class_label)
            i.set_readings(readings)
        return temp_data

    @staticmethod
    def parse_uarff_from_string(string: str, class_id: (int, str) = None) -> 'Data':
        try:
            br = StringIO(string)
        except:
            traceback.print_exc()
            return None
        temp_data = Data.__read_uarff_from_buffer(br)
        br.close()
        if not class_id:
            return temp_data

        return Data.__parse(temp_data, class_id)

    @staticmethod
    def parse_uarff(filename: str, class_id: (int, str) = None) -> 'Data':
        try:
            br = open(filename)
        except:
            traceback.print_exc()
            return None
        temp_data = Data.__read_uarff_from_buffer(br)
        br.close()
        if not class_id:
            return temp_data

        return Data.__parse(temp_data, class_id)

    @staticmethod
    def parse_instances(base_atts: List[Attribute], inst_def: str) -> Instance:
        readings_defs = inst_def.split(',')
        i = Instance()
        if len(readings_defs) != len(base_atts):
            raise ParseException('Missing attribute definition, or value in line ' + inst_def)
        for reading, att in zip(readings_defs, base_atts):
            r = Reading.parse_reading(att, reading)
            i.add_reading(r)
        return i

    @staticmethod
    def parse_attribute(att_def: str) -> Attribute:
        name_boundary = int(att_def.index(' '))
        type = Attribute.TYPE_NOMINAL
        name = att_def[0:name_boundary]
        domain = set()
        untrimmed_domain = re.sub(r'[{}]', '',  att_def[name_boundary:]).split(',')
        for value in untrimmed_domain:
            if value.strip() == Data.REAL_DOMAIN:
                type = Attribute.TYPE_NUMERICAL
                break 
            domain.add(value.replace("'", '').strip())
        return Attribute(name, domain, type)

    def get_instances(self) -> List[Instance]:
        return self.instances.copy()

    def get_attributes(self) -> List[Attribute]:
        return list(self.attributes.values())

    def get_name(self) -> str:
        return self.name

    def get_class_attribute(self) -> Attribute:
        return self.attributes[self.class_attribute_name]  # get last element
