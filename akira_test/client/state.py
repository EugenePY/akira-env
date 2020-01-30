
class DiscreteState(object):
    # only take discrete action
    # last_state
    operation = {"LONG": ["ADD", "OFFSET", "TURN"],
                 "SHORT": ["ADD", "OFFSET", "TURN"],
                 "NEUTRAL": ["LONG", "SHORT", "NEUTRAL"]}

    def _step(self, act):
        pass

    def apply(self, action):
        state = {}

        for symbol, act in action.items():
            state[symbol] = self._step(act)
            self.episode_stack.add(**state[symbol])
