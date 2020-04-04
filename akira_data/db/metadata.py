
# -*- coding: utf-8 -*-
import datetime
import importlib
import pkgutil
import re
from enum import Enum
from pkgutil import walk_packages

import pandas as pd
from marshmallow import fields

from akira_data.db.currency import SymbolEnum
from akira_data.db.db_model import Model
from akira_data.db.events import CountryCode
from akira_data.db.fields import DateTime, EnumType, ParseEnum, Tenor


class AssetClasses(ParseEnum):
    # equity
    EQUITY = "EQUITY"
    # currency
    CCY = "CCY"
    CURNCY = CCY
    CURRENCY = CCY

    # fixed income
    FIXINCOME = "FIXINCOME"

    # eco index
    ECO = "ECO"

    # option related
    OPTION = "OPTION"
    # Index
    INDEX = "INDEX"


class Fields(ParseEnum):
    PX_MID = "PX_MID"
    PX_LAST = "PX_LAST"
    PX_OPEN = "PX_OPEN"
    PX_HIGH = "PX_HIGH"
    PX_LOW = "PX_LOW"
    PX_EXE = "PX_EXE"


class ContractType(ParseEnum):
    FORWRD = "FORWRD"

    ATM = "ATM"
    V = ATM

    RR = "RR"
    R = RR

    BF = "BF"


class MarketQuote(ParseEnum):
    BGNT = "BGNT"
    BGN = "BGN"
    CMPT = "CMPT"
    INTRA15M = "15M"
    INTRA30M = "30M"
    INVT = "INVT"


class Connections(Enum):
    investingdotcom = "akira_data.data.web.InvestingDotComAPI"
    ecoevent = "akira_data.data.web.EcoEventAPI"
    bbg = "akira_data.data.bbg.BBGapiClient"

    def get_connection_cls(self):
        path = self.value.split(".") 
        import_path = ".".join(path[:-1])
        cls_ = path[-1]
        return getattr(importlib.import_module(import_path), cls_)


class Metadata(Model):
    # Parseable
    country = EnumType(CountryCode)
    ccy_symbol = EnumType(SymbolEnum)
    symbol_type = EnumType(AssetClasses)
    contract_type = EnumType(ContractType)
    tenor_unit = EnumType(Tenor)
    market_quote = EnumType(MarketQuote)
    # Not ParseAble
    source = EnumType(Connections)

    @classmethod
    def ticker_pattern(cls, pattern):
        all_patterns = {}
        for k, v in cls._schema_class._declared_fields.items():
            if hasattr(v, "enum"):
                if issubclass(v.enum, ParseEnum):
                    all_patterns[k] = "(?P<{}>".format(k) + \
                        v.enum.pattern().replace("(", "")
        return pattern.format(**all_patterns)

    @classmethod
    def from_symbol(cls, ticker_string,
                    pattern="{country}{ccy_symbol}{field}{asset_type}",
                    **kwarg):
        # make pattern from input pattern, and predefine enum
        pattern = cls.ticker_pattern(pattern)
        prog = re.compile(pattern)
        # convert input string into upper case
        match = prog.match(ticker_string)
        if match:
            gruopdict = match.groupdict()
        else:
            gruopdict = {}
        gruopdict.update(kwarg)

        if match:
            return cls(**gruopdict)
        else:
            raise ValueError(f"pattern={pattern} no match for {ticker_string}.")
        
