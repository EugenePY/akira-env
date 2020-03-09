import collections
from marshmallow import Schema, fields
import numpy as np


class Entry(dict):
    #price = fields.Float()
    #position = fields.Float()
    def __init__(self, price: float, position: float):
        self.price = price
        self.position = position
        super(Entry, self).__init__({"price": price, "position": position})

    def direction(self):
        return np.sign(self.price * self.position)


class Position(collections.defaultdict):
    """Trading Position, and PNL

    nominal: in USD
    """

    def __init__(self, entry: dict, *arg, **kwarg):
        super(Position, self).__init__(
            entry, lambda x: Entry(price=0, position=0),
            *arg, **kwarg)

    @classmethod
    def reset(cls, entry):
        return cls(entry)

    def update(self, entry_dict: dict):
        entry_dict = {k: self._update_entry(self.get(k), entry)
                      for symbol, entry in entry_dict.items()}
        return super().update(entry_dict)

    def _update_entry(self, state, new):
        if state.direction() == new.direction():
            new_pos = state.position + new.position
            alpha = state.position/(new_pos)
            out =  Entry(price=alpha * state.price + (1 - alpha) * new.price,
                        position=new_pos)
            out["pnl"] = 0.
        else:
            pass


    def mark2market(self, mkt_price):
        pass


if __name__ == "__main__":
    def test():
        trades = []
        for i in range(10):
            trade = {i: Entry(price=np.exp(np.random.normal()),
                              position=np.random.randint(-10, 10))
                     for i in ["AUDUSD", "USDKRW", "USDJPY"]}
            trades.append(trade)
