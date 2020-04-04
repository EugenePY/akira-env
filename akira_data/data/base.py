import abc


class API(metaclass=abc.ABCMeta):
    """API only provide data Query
    """

    @property
    def name(self):
        return self.__class__.__name__

    @abc.abstractmethod
    def get(self, variable, start, end):
        pass

    @abc.abstractmethod
    def get_batch(self, variables, start, end):
        pass

    def status(self):
        pass