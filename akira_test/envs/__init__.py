
def collect_input_output(fn):
    def wrapper_fn(self, *arg, **kwarg):
        out = fn(self, *arg, **kwarg)
        self.guess_record.append(
            {"fn_call": fn.__name__,
             "input": kwarg,
             "observation": out}
        )
        return out
    return wrapper_fn