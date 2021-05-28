# AUTOGENERATED! DO NOT EDIT! File to edit: src/reading.ipynb (unless otherwise specified).

__all__ = ['Reading']

# Cell
import re
from typing import List

from .attribute import Attribute
from .value import Value

# Cell
class Reading:
    def __init__(self, base_att: Attribute, values: List[Value]):
        self.base_att = base_att
        self.values = values

    def get_base_att(self) -> Attribute:
        return self.base_att

    def get_values(self) -> List[Value]:
        return self.values

    def get_most_probable(self) -> Value:
        confidence = [value.get_confidence() for value in self.values]
        highest_conf = max(confidence)
        index = confidence.index(highest_conf)
        return self.values[index]

    def __str__(self):
        result = ''
        for value in self.values:
            result += value.get_name() + '[' + str(value.get_confidence()) + '];'
        result = result[:-1]  # delete the last semicolon ';'
        return result

    @staticmethod
    def parse_reading(base_att: Attribute, reading_def: str) -> 'Reading':  # TODO throws ParseException, docstring
        """The method parse the reading which has to be formatted in the following way:
        v1[probability];v2[probability];...;vn[probability]
        The number of values has to correspond to the size of the domain of base_att.
        In case the reading does not cover all the values, remaining values are assigned probability
        according to uniform distribution.

        Args:
            base_att (Attribute): the attribute for which the reading is made
            reading_def (str): the reading definition
        Raises:
            ParseException: probability greater than 1
        Returns:
            reading: the reading
        """
        vals = reading_def.replace(' ', '').split(';')
        values = []
        total_prob = 0

        for v in vals:
            print(v)
            val_prob = re.split(r'[\[\]]', v)
            name = val_prob[0].strip()
            confidence = 1
            if name == '?':
                break
            if len(val_prob) > 1:
                confidence = float(val_prob[1].strip())
            values.append(Value(name, confidence))
            total_prob += confidence

        if total_prob > 1:
            pass
            # raise ParseException("Probability greater than 1 in " + reading_def)

        # check if there are some missing values to assign them uniform distribution
        if base_att.get_type() == Attribute.TYPE_NOMINAL:
            val_names = [v.get_name() for v in values]
            remaining = base_att.get_domain().copy()
            remaining -= set(val_names)

            # find out if there is any probability left for missing values, if any
            if remaining:
                uniform_prob = (1 - total_prob) / len(remaining)
                for rv in remaining:
                    values.append(Value(rv, uniform_prob))

        elif base_att.get_type() == Attribute.TYPE_NUMERICAL:
            pass

        return Reading(base_att, values)
