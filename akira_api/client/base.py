import abc
import os
import numpy as np
from arctic import Arctic
import pandas as pd
from loguru import logger


class Action(object):

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key, 0)

    def sample(self):
        return np.random.normal(size=len(self.variables))


class Discrete(object):
    # time dependent action
    space = {"LONG": ["ADD_POSITION", "PT", "STOP_LOSS", ""],
             "SHORT": ["ADD_POSITION", "PT", "STOP_LOSS"],
             "NEUTRAL": ["LONG", "SHORT", "NEUTRAL"]}

    def sample(self, state):
        pass


class State(object):
    def __init__(self, ndim):
        self._ndim = ndim

    def sample(self):
        return np.random.random(size=self._ndim)

    def fetch(self, date_range):
        # fetch data from mongo server
        data = {}
        lib = self.store.get_library(self.libname)
        for symbol in self.symbols:
            data[symbol] = lib.read(
                symbol, date_range=date_range).data
        data = pd.concat(data, axis=1)
        return data


class Indexer:
    def __init__(self, idx, n_episode):
        self.idx = idx
        self.n_episode = n_episode
        self.reset()

    def __next__(self):
        self.step += 1
        val = self.seq[self.step]
        return val

    def reset(self):
        start = np.random.choice(
            range(len(self.idx)-self.n_episode))
        self.seq = self.idx[start:start+self.n_episode]
        self.step = 0
        return self.seq[self.step]

    def get_offset(self, offset):
        if offset < 0:
            raise ValueError("Offeset only allow" +
                             " positive Interger. Got {}.".format(offset))
        return self.seq[self.step-offset]


class StateStack(object):

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


class EndogState(State):
    """Position: Stack of Actions
    """
    mongo_uri = os.environ.get("MONGO_URI", "localhost")
    store = Arctic(mongo_uri)

    def __init__(self, variables, date_range, n_episode, libname, generator=None):
        self.variables = variables
        self.symbols = [var.symbol for var in self.variables]
        self.libname = libname

        self.data = self.fetch(date_range)

        self.episode_stack = StateStack(
            columns=["price", "cost",
                     "inv", "pnl", "return", "act", "mk2mkt_pnl"],
            ids=["timestep", "symbol"])

        if generator is None:
            self.generator = Indexer(self.data.index, n_episode=n_episode)

        else:
            if not issubclass(type(generator), Indexer):
                raise ValueError("gernerator should be subclass of {}. Got {}.".format(
                    type(Indexer), type(generator)))

            self.generator = generator

        self.reset()

    def reset(self):
        self.generator.reset()
        self.episode_stack.reset()

    def step(self, action, nan_check=False):
        timestep = next(self.generator)
        timestep_last = self.generator.get_offset(offset=1)
        prices = self.data.loc[timestep].loc[(slice(None), "PX_OPEN")]

        for symbol in self.symbols:
            price = prices[symbol]

            entry_last = self.episode_stack.query(
                tuple([timestep_last, symbol]))
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

            self.episode_stack.add(entry)

        return self.episode_stack[timestep]

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
                cost = price = 0.

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
                mk2mkt_pnl = cost = price = 0.

        return cost, pnl, _r, price, mk2mkt_pnl, inv

    @property
    def state(self):
        return self.episode_stack.get_offset(offset=1)

    @property
    def state_last(self):
        return self.episode_stack.get_offset(offset=2)


class ExogState(EndogState):
    # Other information beside position
    def reset(self):
        self.episode_stack.reset()
        self.generator.reset()

        data = self.data.loc[:self.generator.seq[0]].shift(
            1)  # delayed information
        state = self.episode_stack[-1]
        return state, data

    def step(self):  # which cannot controll directly
        timestamp = next(self.generator)
        return data[timestamp]


class Env(metaclass=abc.ABCMeta):

    def info(self):
        """exog variable: source of information
        """
        pass

    def endog(self):
        pass

    @abc.abstractmethod
    def reset(self):
        info = self.info.reset()
        obs = self.endog.reset()
        self.last_obs = obs
        self.timestep = 0
        return obs, info

    def last_obs(self):
        pass

    def step(self, action):
        info = self.info.step(t)

        # calculate reward
        reward = self.reward(self.endog.state, action)

        # state forward
        state, last_state = self.endog.step(action)

        return reward, state, done, info
