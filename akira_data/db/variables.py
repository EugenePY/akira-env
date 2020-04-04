import abc

from arctic import TICK_STORE, VERSION_STORE
from marshmallow.fields import String

from akira_data.db.db_model import Model, NestedModel
from akira_data.db.fields import EnumType
from akira_data.db.metadata import Metadata, Connections
from .currency import ParseEnum


class Store(ParseEnum):
    version = VERSION_STORE
    ticker = TICK_STORE


# Integrate with data validation
class Variable(Model):
    metadata = NestedModel(Metadata)
    symbol = String()
    pattern = String()
    libname = String()
    store = EnumType(Store)


class VariablePool(metaclass=abc.ABCMeta):
    # Dataset Intergration with API
    # Generate, Symbol, metadata, data
    name = None
    fields = ["PX_LAST"]
    pattern = "{ccy} {market_quote} {symbol_type}"
    store = "version"
    libname = None
    source = None

    # msic
    start = "19950101"  # start date of dataset

    def __new__(cls, *arg, **kwarg):
        cls.variables = cls.make_variables()
        cls.conn = Connections[cls.source].get_connection_cls()()
        return super(VariablePool, cls).__new__(cls, *arg, **kwarg)

    def __getitem__(self, symbol):
        return self.variables[symbol]

    def __setitem__(self, symbol, value):
        if isinstance(value, Variable):
            self.variables[symbol] = value
        else:
            print("value:{} not set".format(value))

    @abc.abstractclassmethod
    def make_variables(cls):
        """Modify this
        """
        return []

    def get(self, symbol, start, end):
        return self.conn.get(self[symbol], start, end)

    def get_batch(self, symbols, start, end):
        var_ = [self[symbols] for symbol in symbols]
        return self.conn.get_batch(var_, start, end)

    def save(self, arctic_lib):
        for symbol, var in self.variables.item():
            arctic_lib[self.libname].write_metadata(
                symbol, metadata=var.metadata.dump())
