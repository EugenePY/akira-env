import numpy as np
from .base import Base
import sqlachemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref


class BaseActionSpace(object):
    """Define Action Rules
    """

    def sample(self):
        amounts = np.random.normal(size=len(self.variables))
        trades = []
        for amount, symbol in zip(amounts, self.variables.keys()):
            Trade(symbol=symbol, amount=amount,
                  self.__class__.__name__)
        return trades

    def valid(self):
        pass

    @property
    def action_id(self):
        self._action_id = "simple"


class Trade(Base):
    exp_id = relationship("Experiment", backref=backref("experiment"))
    model = sa.Column(sa.String)
    action_space = sa.Column(sa.String)
    symbol = sa.Column(sa.String)
    amount = sa.Column(sa.Interger)
    datetime = sa.Column(sa.Utcdatetime)

    def __repr__(self):
        return "< Trades: symbol = {symbol}, amount = {amount},\
            action_space = {action_space} >".format(
            symbol=self.symbol, amount=self.amount,
            action_space=self.action_space
        )
