import numpy as np


class RandomAgent(object):
    def __init__(self, symbols):
        self.symbols = symbols

    def partial_fit_act(self, data):
        return {s: np.random.randint(-1, 1) for s in self.symbols}

    def fit_act(self, data):
        return {s: np.random.randint(-1, 1) for s in self.symbols}
