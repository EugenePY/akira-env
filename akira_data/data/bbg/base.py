# -*- coding: utf-8 -*-
import abc
import datetime
from functools import reduce

import requests
from akira_data.db import Variable, VariablePool
from akira_data.data.base import API


class BBGVariablePool(VariablePool):
    libname = "bloomberg"
    store = "version"
    source = "bbg"
    fields = ["PX_LAST"]

    def get(self, symbol, start, end):
        return self.conn.get(symbol, self.fields, start, end)

    @classmethod
    def apply(cls, symbol):
        return metadata.Metadata.from_symbol(
            symbol.upper(), cls._pattern,
            source=cls.source, fields=cls._fields)

    @classmethod
    def make_variables(cls):
        variables = {}
        for symbol in cls.symbols():
            meta = cls.apply(symbol)
            var = metadata.Variable(symbol=symbol, metadata=meta.dump(),
                                    libname=cls.libname, store=cls.store)
            variables[symbol] = var
        return variables

    @classmethod
    def symbols(cls):
        for i in range(10):
            yield i
