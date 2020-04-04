
import re
from datetime import datetime
from enum import Enum, Flag

import pandas as pd
from marshmallow import Schema, fields
from marshmallow.validate import OneOf, ValidationError

# for taging


class ParseEnum(Enum):
    @classmethod
    def pattern(cls):
        return ("(" + "|".join(list(cls.__members__.keys())) + ")").upper()

    @classmethod
    def _missing_(cls, value):
        return getattr(cls, value)


def parsing_validator(prog, input_string):
    out = prog.match(input_string)
    if out is None:
        raise ValidationError(
            "input string should satisfy pattern={}".format(prog.pattern))


tenor_map = {"YR": 1, "M": 1./12, "W": 7./12., "ON": 1./360}


class Tenor(ParseEnum):
    YEAR = "YR"
    Y = YEAR
    YR = YEAR

    MONTH = "M"
    MON = MONTH
    M = MONTH

    WEEK = "W"
    W = WEEK

    ON = "ON"
    DAY = ON
    D = ON

    def __float__(self):
        return tenor_map[self.value]


class EnumType(fields.Field):
    """Validates against a given set of enumerated values."""

    def __init__(self, enum, *args, **kwargs):
        super(EnumType, self).__init__(*args, **kwargs)
        self.enum = enum
        self.validators.insert(0, OneOf([v.name for v in self.enum]))

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str):
            return self.enum[value].name
        else:
            return value.name

    def _deserialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str):
            return self.enum[value]
        else:
            return value

    def _validate(self, value):
        if type(value) is self.enum:
            super()._validate(value.name)
        else:
            try:
                super()._validate(self.enum[value].name)
            except Exception:
                raise ValidationError("Input {} is not in Enum set".format(
                    value))


class DateTime(fields.DateTime):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data, **kwargs)