import numpy as np
from .state import BaseState


class BaseActionSpace(object):
    """Define Action Rules
    """
    action_id = "simple"
    _state = None

    def sample(self):
        amounts = np.random.normal(size=len(self.variables))
        trades = {}
        for amount, symbol in zip(amounts, self.variables.keys()):
            trades[symbol] = amount
        return trades

    @property
    def state(self):
        return self._state

    @state.setter
    def set_state(self, state):
        # check state
        self._state = state