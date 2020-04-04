from akira_data.db.events import CountryCode, COUNTRY2SYMBOL
from akira_data.db.metadata import Metadata, Connections
from akira_data.db.variables import Variable, VariablePool


class InvestingDotVariablePool(VariablePool):
    libname = "investing"
    store = "version"
    source = "investingdotcom"

    @classmethod
    def make_variables(cls):
        usdx = ["CAD", "CHF", "JPY", "KRW", "TWD", "IDR", "INR"]
        xusd = ["AUD", "NZD", "GBP", "EUR"]
        quotes = ["INVT"]
        symbol_type = "Curncy"
        pattern1 = "USD{ccy_symbol} {market_quote} {symbol_type}"
        pattern2 = "{ccy_symbol}USD {market_quote} {symbol_type}"

        templates = {pattern1: usdx,
                     pattern2: xusd}
        variables = {}

        for pattern, token in templates.items():
            for t in token:
                for q in quotes:
                    symbol = pattern.format(
                        ccy_symbol=t, market_quote=q,
                        symbol_type=symbol_type)
                    meta = Metadata.from_symbol(symbol.upper(),
                                                pattern=pattern,
                                                source=cls.source)
                    var = Variable(symbol=symbol, metadata=meta.dump(),
                                   libname=cls.libname, store=cls.store)
                    variables[symbol] = var

        return variables

    def get_batch(self, symbols, start, end):
        # this sould return {symbol: data}
        req_arg_symbol = {symbol.split(" ")[0]: symbol for symbol in symbols}
        data = self.conn.get_batch(list(req_arg_symbol.keys()),
                                   start, end, resolution="1D")
        return {req_arg_symbol[k]: v for k, v in data.items()}


class IntraDayVariablePool(VariablePool):
    libname = "intraday"
    store = "ticker"
    source = "investingdotcom"

    @classmethod
    def make_variables(cls):
        usdx = ["CAD", "CHF", "JPY", "KRW", "TWD", "IDR", "INR"]
        xusd = ["AUD", "NZD", "GBP", "EUR"]
        quotes = ["INTRA15M"]
        supported_resulution = ['1', '5', '15', '30', '60', '1D', '1W', '1M']
        # data is JSON having format {s: "status" (ok, no_data, error),
        # v: [volumes], t: [times], o: [opens], h: [highs], l: [lows], c:[closes], nb: "optional_unixtime_if_no_data"}

        symbol_type = "Curncy"
        pattern1 = "USD{ccy_symbol} {market_quote} {symbol_type}"
        pattern2 = "{ccy_symbol}USD {market_quote} {symbol_type}"

        templates = {pattern1: usdx,
                     pattern2: xusd}
        variables = {}

        for pattern, token in templates.items():
            for t in token:
                for q in quotes:
                    symbol = pattern.format(
                        ccy_symbol=t, market_quote=q,
                        symbol_type=symbol_type)
                    meta = Metadata.from_symbol(symbol.upper(),
                                                pattern=pattern,
                                                source=cls.source)
                    var = Variable(symbol=symbol, metadata=meta.dump(),
                                   libname=cls.libname, store=cls.store)
                    variables[symbol] = var

        return variables

    def get_batch(self, symbols, start, end):
        # this sould return {symbol: data}
        req_arg_symbol = {symbol.split(" ")[0]: symbol for symbol in symbols}
        data = self.conn.get_batch(list(req_arg_symbol.keys()),
                                   start, end, resolution="15")

        return {req_arg_symbol[k]: v for k, v in data.items()}

    def get(self, symbol, start, end):
        data = self.conn.get(symbol.split(" ")[0], start, end, resolution="15")
        return data


class EcoEventVariablePool(VariablePool):
    libname = "investing"
    store = "version"
    source = "ecoevent"

    @classmethod
    def make_variables(cls):
        countries = ['Australia', 'Canada', 'China', 'Euro Zone', 'Germany',
                     'France', 'Italy', 'Japan', 'Sweden', 'New Zealand',
                     'United Kingdom', 'United States',
                     'Taiwan', "KR", "CA", "CN", "Thailand"]

        symbol_type = "ECO"
        pattern = "EE{country} {symbol_type}"
        variables = {}
        for t in countries:
            symbol = pattern.format(
                country=CountryCode(t).name, symbol_type=symbol_type)
            meta = Metadata.from_symbol(
                symbol.upper(), pattern=pattern,
                source=cls.source,
                ccy_symbol=COUNTRY2SYMBOL[CountryCode(t)])
            var = Variable(symbol=symbol, metadata=meta.dump(),
                           libname=cls.libname, store=cls.store)
            variables[symbol] = var

        return variables

    def get_batch(self, symbols, start, end):
        arg = {self[symbol].metadata.country.name: symbol for symbol in symbols}
        data = self.conn.get_batch(list(arg.keys()), start, end)
        return {arg[k]: v for k, v in data.items()}

    def get(self, symbol, start, end):
        return list(self.conn.eco_event_loop(self[symbol].metadata.country.name, start, end))
