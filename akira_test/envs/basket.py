from ..models.env import BaseEnv


class BasketEnv(BaseEnv):
    """Basic Trading Enviroment 

    the information cut time is @9:00 utc+8, 

    Excution price 
        Mid price, between 10:00~15:00

    Reward:
        Risk Adjusted Reward, Sharpe Ratio
    """
    env_id = "basket"

    def __init__(self, exog_state, action_space):
        self._exog_space = exog_state
        self._action_space = action_space

        self._data = self._exog_space.fetch(
            date_range[0], date_range[1])

    def reset(self):
        pass

    def step(self, action):
        pass

    def reward(self, endog_state, action):
        pass

    def report(self):
        """ Exog Variable, Endog Variable, Action
        """
        pass
