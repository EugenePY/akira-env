import os

import marshmallow as ma
import pandas as pd
from loguru import logger
from arctic import Arctic
from arctic.date import DateRange
import numpy as np

from ..models.actions import BaseActionSpace
from ..models.env import BaseEnv
from ..models.state import BaseState
from ..serialization import Model
from . import collect_input_output


class Indexer:
    idx_id = "base"
    step = 0

    def __init__(self, idx, n_episode, mode="test"):
        assert n_episode > 0
        self.idx = idx
        self.n_episode = n_episode
        self.reset()

    def __next__(self):
        self.step += 1
        try:
            val = self.seq[self.step]
        except IndexError:
            raise IndexError("Out of Index")
        return val

    def reset(self):
        # random choice the stating point
        if mode == "test":
            start = np.random.choice(
                range(len(self.idx)-self.n_episode))
            self.seq = self.idx[start:start+self.n_episode]
            self.step = 0
        elif mode == "deploy":
            pass
        return self.seq[self.step]

    def get_offset(self, offset):
        if offset < 0:
            raise ValueError("Offeset only allow" +
                             " positive Interger. Got {}.".format(offset))
        if self.step - offset < 0:
            return None

        return self.seq[self.step-offset]

    def last(self):
        return self.step == self.n_episode - 1


class StateStack(object):
    """Record trading histroy
    """

    def __init__(self, ids, columns):
        self.__id__ = ids
        self.__columns__ = columns
        self.reset()

        self.empty = {i: 0 for i in self.__columns__}

    def add(self, entry):
        idx = tuple([entry.pop(id_) for id_ in self.__id__])
        self.stack[idx] = {col: entry[col] for col in self.__columns__}

    def reset(self):
        self.stack = {}

    def query(self, key):
        return self.stack.get(key, self.empty)

    def __getitem__(self, timestep):
        out = {}
        for k, v in self.stack.items():
            if k[0] == timestep:
                out[k[1]] = v
        return out

    def __str__(self):
        return str(self.stack)


class Datahandler(object):
    data_cached = None
    mongo_uri = os.environ.get("MONGO_URI", "localhost")
    store = Arctic(mongo_uri)

    def __init__(self, symbols, libname):
        self.libname = libname

    def fetch(self, start, end=None):
        # fetch data from mongo server
        date_range = DateRange(start=start, end=end)
        data = {}
        lib = self.store.get_library(self.libname)
        for symbol in self.symbols:
            data[symbol] = lib.read(
                symbol, date_range=date_range).data
        data = pd.concat(data, axis=1).fillna(method="ffill")

        return data

    def get(self, index, cols):
        if index not in self.data_cached.index:
            logger.info("Datetime Index={} not found".format(
                index))
            # update latest data
            self.data_cached = self.data_cached.append(
                self.fetch(index, None))  # fetch all afterward
        return self.data_cached.loc[index, cols]


class TradingEnvSchema(ma.Schema):
    variables = ma.fields.List(ma.fields.Str)
    start = ma.fields.DateTime()
    end = ma.fields.DateTime()
    n_episode = ma.fields.Integer()
    info = ma.fields.List(ma.fields.Str, nullable=True)
    genertor = ma.fields.Str(nullable=True)


class EnvRewarder(object):
    # output signal, input signal
    def dump(self):
        pass


class TradingEnv(BaseEnv):
    """
    TradingSimulator: 
    Timestep: Each Trading Date.

    Reset, initial date that your start to trade
    step
    """
    env_id = "trading"
    schema = TradingEnvSchema

    def __init__(self, symbols, start, end, n_episode, libname, info=None,
                 generator=None):
        self.symbols = symbols

        # database
        self.datahandler = Datahandler(symbols, libname)
        self.datahandler.fetch(start)  # we query all latest data

        # prepare stacks
        self.episode_stack = StateStack(
            columns=["price", "cost",
                     "inv", "pnl", "return", "act", "mk2mkt_pnl"],
            ids=["timestep", "symbol"])

        self.n_episode = n_episode

        if generator is None:
            generator = Indexer(self.data.index, n_episode=n_episode)

        else:
            if not issubclass(type(generator), Indexer):
                raise ValueError("gernerator should be "
                                 "subclass of {}. Got {}.".format(
                                     type(Indexer), type(generator)))

        self.generator = generator

        if info is None:
            self.info = {}

        self.reset()

    def reset(self):
        self.generator.reset()
        self.episode_stack.reset()
        entry = self.episode_stack[self.genertor.timestep]
        entry["done"] = False
        entry["info"] = {}
        return entry

    def step(self, action, nan_check=False):

        timestep = self.timestep
        timestep_last = self.generator.get_offset(offset=1)

        out = {"done": False, "info": {}}

        # check terminal condtion
        if self.generator.last():
            # Terminal Condtion met.
            action = {}
            # cleanup all position
            for sym in self.symbols:
                entry_last = self.episode_stack.query(
                    tuple([timestep_last, sym]))
                action[sym] = - entry_last["inv"]
            out["done"] = True

        # check if the next date is settlement date
        if self.generator.step == self.n_episode - 2:
            out["info"] = {"status": "cleanup"}

        prices = self.datahandler.get(
            index=timestep, cols=[(slice(None), "PX_OPEN")])

        r = 0

        for symbol in self.symbols:
            price = prices[symbol]
            entry_last = self.episode_stack.query(
                tuple([timestep_last, symbol]))

            # check price
            if not pd.isnull(price):
                # the px is see able
                act = action.get(symbol, 0)
            else:
                # the px is not seeable, offset the trade
                act = 0

            # handle execution pnl and cost
            cost, pnl, _r, price, mk2mkt_pnl, inv = self._cost_and_position(
                cost_last=entry_last["cost"],
                inv_last=entry_last["inv"],
                price=price, act=act)

            entry = {"timestep": timestep, "symbol": symbol, "price": price,
                     "cost": cost, "pnl": pnl, "mk2mkt_pnl": mk2mkt_pnl,
                     "return": _r, "inv": inv, "act": act}

            if nan_check:
                if any(pd.isnull(list(entry.values()))):
                    raise ValueError("Value contains nan")
            _r = entry["return"] + entry["mk2mkt_pnl"]
            r += _r
            self.episode_stack.add(entry)
            out[symbol] = {"reward": _r,
                           "inv": entry["inv"]}
        out["reward"] = r
        # update state
        try:
            next(self.generator)
        except IndexError:
            logger.debug("End episode.")

        return out

    def _cost_and_position(self, cost_last, inv_last, price, act):
        # State Action Map,
        # State->, Long: position > 0, Short: position < 0, Neutral: position = 0
        # Long and Short: Add Position, Offset Position, Turn to opposite position(Long to Short, Short to Long)
        # Neutral: Long, Short, Neutral

        # last State: Neutral
        if cost_last == 0 and inv_last == 0:
            # Action: Neutral
            if act > 0:
                # Action: Long
                cost = price = price
            elif act < 0:
                # Action: Short
                cost = price = price
            else:
                # Action: Neutral
                cost = 0.

            inv = act

            pnl = mk2mkt_pnl = 0.
            _r = 0.

        else:
            # Last Action: Long or Short
            _r = (price/cost_last - 1)  # mark2mkt return

            if pd.isnull(_r):
                raise ValueError("Return not defined.")

            if np.sign(inv_last) == np.sign(act):
                # Action: Adding Position
                alpha = (inv_last/(inv_last+act))
                cost = cost_last * alpha + price * (1-alpha)
                pnl = 0
                inv = inv_last + act
                mk2mkt_pnl = inv * _r
            else:
                # Action: Offset the position
                pop_out = abs(act)
                inventroy = abs(inv_last)

                # spot pnl
                if pop_out > inventroy:
                    # Action: Turn to oppositie position
                    cost = price
                    inv = inv_last - act
                    mark2mkt = 0.
                else:
                    # Action: Neutral or Keep the position
                    inv = (inv_last - act)
                    cost = cost_last
                    mk2mkt_pnl = inv * _r
                pt_amount = min(inv_last, pop_out)  # offset all the inv
                # the remain put into opposite direction
                pnl = (pt_amount) * _r

            inv = inv_last + act

            if np.isclose(inv, 0):
                # if today donot have position (Neutral)
                mk2mkt_pnl = cost = 0.

        return cost, pnl, _r, price, mk2mkt_pnl, inv

    @property
    def timestep(self):
        return self.generator.get_offset(offset=0)

    @property
    def timestep_last(self):
        return self.generator.get_offset(offset=1)

    @classmethod
    def serialize_env(cls, env):
        return cls.schema().dump(env)

    @classmethod
    def deserialize_env(cls, data):
        return cls(**data)

    def generate_tearsheet(self):
        return pd.DataFrame(self.episode_stack.stack).T
