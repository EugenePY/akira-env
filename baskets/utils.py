import click
from functools import update_wrapper, wraps
import yaml


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """
    def new_func(*args, **kwargs):
        @wraps(f)
        def processor(stream):
            return f(stream, *args, **kwargs)
        return processor
    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """
    @processor
    def new_func(stream, *args, **kwargs):
        for item in stream:
            yield item

        for item in f(*args, **kwargs):
            yield item
    return update_wrapper(new_func, f)


def apply(f):
    """simillar with proccessor but proccess each itemof each generator.
    """
    @processor
    def new_func(stream, *args, **kwargs):
        for item in stream:
            yield f(item, *args, **kwargs)
    return update_wrapper(new_func, f)


def using_specfile(f):
    @click.option("-f", "--file", "file", type=click.File("r"))
    @wraps(f)
    def new_func(*arg, **kwarg):
        spec = yaml.load(kwarg["file"], Loader=yaml.FullLoader)
        kwarg.update(spec) # overide all specs
        return f(*arg, **kwarg)
    return new_func
        