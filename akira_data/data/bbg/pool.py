from akira_data.db import VariablePool, Metadata, Variable
from akira_data.data.bbg.base import BBGVariablePool
from akira_data.db.events import CountryCode
import re


class SpotUniverse(BBGVariablePool):
    name = "spot_universe"
    store = "version"
    libname = "bloomberg"

    ccys = ["CNH", "CNY", "KRW", "INR", "IDR", "SGD", "TWD"]

    USDX = ["CHF", "CAD", "JPY", "SEK"] + ccys
    EMEA = ["ZAR", "HUF", "SKK", "PLN", "RUB", "TRY"]
    LATAM = ["PEN", "BRL", "ARS", "MXN"]

    USDX += EMEA
    USDX += LATAM
    QUOTES = ["CMPT", "BGNT", "BGN"]  # TOKYO TIME
    format_usdx = "USD{} {} Curncy"
    USD = ["DXY"]
    format_xusd = "{}USD {} Curncy"
    XUSD = ["AUD", "GBP", "NZD", "EUR"]
    fields = ["PX_LAST", "PX_MID", "PX_OPEN", "PX_HIGH", "PX_LOW"]

    source = "bbg"

    @classmethod
    def make_variables(cls):
        variables = {}

        for ccy in cls.ccys:
            for q in cls.QUOTES:
                symbol = cls.format_usdx.format(ccy, q)
                meta = Metadata.from_symbol(symbol.replace("USD", "").upper(),
                                            pattern="{ccy_symbol} {market_quote} {symbol_type}",
                                            source="bbg")
                variables[symbol] = Variable(symbol=symbol,
                                             metadata=meta.dump(),
                                             store=cls.store,
                                             libname=cls.libname)

        for ccy in cls.XUSD:
            for q in cls.QUOTES:
                symbol = cls.format_xusd.format(ccy, q)
                meta = Metadata.from_symbol(symbol.replace("USD", "").upper(),
                                            pattern="{ccy_symbol} {market_quote} {symbol_type}",
                                            source="bbg")
                variables[symbol] = Variable(symbol=symbol,
                                             metadata=meta.dump(),
                                             store=cls.store,
                                             libname=cls.libname)

        return variables


class REER(BBGVariablePool):
    name = "reer"
    code = ["EU", "NZ", "AU", "CA", "US",
            "SE", "GB", "JP", "TW", "CN", "KR"]
    format_ = "BIS{}{}R Index"
    libname = "bloomberg"
    source = "bbg"
    store = "version"
    fields = ["PX_LAST"]

    @classmethod
    def make_variables(cls, type_="B"):
        variables = {}
        for i in cls.code:
            symbol = cls.format_.format(type_, i)
            meta = Metadata.from_symbol(symbol.upper(),
                                        pattern="BISB{country}R {symbol_type}",
                                        source=cls.source)
            var = Variable(symbol=symbol, metadata=meta.dump(),
                           libname=cls.libname, store=cls.store)
            variables[symbol] = var
        return variables


class CITI_REER(BBGVariablePool):
    code = ["EU", "NZ", "AU", "CA", "US",
            "CH", "GB", "JP", "TW", "CN", "KR"]
    name = "citi_reer"

    @classmethod
    def symbols(cls, type_="B"):
        cls._pattern = "CTTW{country}R" + type_ + " {symbol_type}"
        for i in cls.code:
            yield cls._pattern.format(country=i, symbol_type="Index")


# Zero-Coupon
class ZERO_RATE(BBGVariablePool):
    name = "zero_coupon"
    template = "{header}{tenor} Index"
    format_ = {
        "GE": {"header": "F910", "suffix": "Index",
               "tenor": ["06M", "01Y", "02Y",
                         "03Y", "04Y", "05Y",
                         "07Y", "10Y", "15Y",
                         "20Y", "30Y"]}
    }
    Y = 360
    unit = {"M": 30./Y, "Y": Y/Y, "W": 7./Y}

    headers = {"FR": "I014", "SF": "I082",
               "GB": "I022", "NZ": "F250",
               "AU": "I063", "CA": "I007",
               "US": "F082",
               "IDR": "I266",
               "GREEK": "I156",
               "SP": "I061",
               "IT": "I040",
               "JP": "I018"}

    for k, v in headers.items():
        format_[k] = {
            "header": headers[k],
            "tenor": format_["GE"]["tenor"]}

    @staticmethod
    def symbols(cls):

        def _rename(x, prog):
            _, num, unit = prog.match(x).groups()
            num = int(num)
            t = num*cls.unit[unit]
            return t

        for k, v in cls.format_.items():

            cls.country = CountryCode(k).name

            format_ = "({header})({num})({unit}) Index".format(
                header=cls.format_[k]["header"],
                num="[0-9]*", unit="|".join(cls.unit.keys())
            )
            prog = re.compile(format_)

            for t in v["tenor"]:
                symbol = cls.template.format(
                    header=v["header"], tenor=t)
                cls.tenor = _rename(symbol, prog)
                yield symbol

    @staticmethod
    def apply(cls, symbol):
        return Metadata.from_symbol(symbol, pattern="{header}{tenor} Index",
                                    tenor=cls.tenor, fields=cls.fields,
                                    country=cls.country)
