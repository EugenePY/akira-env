from ..models.env import BaseEnv
import numpy as np


def collect_input_output(fn):
    def wrapper_fn(self, *arg, **kwarg):
        out = fn(self, *arg, **kwarg)
        self.guess_record.append(
            {"fn_call": fn.__name__,
             "input": [arg, kwarg],
             "observation": out}
        )
        return out
    return wrapper_fn


class SimpleGuessingEnv(BaseEnv):
    env_id = "guess_num"
    guess_record = []
    __init_arg__ = ("answer", "max_num_guess")
    __data_arg__ = ("guess_record", "env_id")

    def __init__(self, max_num_guess=5, random_max=100):
        self.answer = np.random.randint(random_max)
        self.max_num_guess = max_num_guess

    @collect_input_output
    def reset(self):
        self.num_guess = 0
        return {"num_guess": self.num_guess, "correct": False, "done": False}

    @collect_input_output
    def step(self, action):
        guess = action["answer"]
        self.update()
        if guess == self.answer:
            correct = True
        else:
            correct = False

        if correct or self.num_guess >= self.max_num_guess:
            done = True
        else:
            done = False

        if guess > self.answer:
            info = "lower"
        elif guess < self.answer:
            info = "higher"
        else:
            info = 0

        return {"reward": correct*1,
                "num_guess": self.num_guess,
                "info": {"away_from_answer": info},
                "done": done}

    def update(self):
        self.num_guess += 1

    @classmethod
    def serilized_env(cls, env):
        data = {}
        for k in cls.__init_arg__:
            data[k] = getattr(env, k)

        for k in cls.__data_arg__:
            data[k] = getattr(env, k)

        return data

    @classmethod
    def deserialize_env(cls, env_dict):
        arg = {}
        for k in cls.__init_arg__:
            arg[k] = env_dict[k]

        env = cls(**arg)
        for k in cls.__data_arg__:
            setattr(env, k, env_dict[k])
        return env
