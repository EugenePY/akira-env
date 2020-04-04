import click
from baskets.src.transforms import (
    chi2normal_transformation, percentile_score, dropna,
    resample_return, columns_selector, stdout)

from baskets.utils import generator, processor, apply
import pandas as pd
import types


@click.group(chain=True)
def data_pipeline():
    """Data-Pipeline
    """
    pass


@data_pipeline.command("open")
@click.option('-i', '--inputs', 'inputs', type=click.Path(),
              multiple=True, help='inputfile to open.')
@click.option('-x', '--header', 'index_col', multiple=True, type=int)
@generator
def make_open(inputs, index_col):
    for input_ in inputs:
        try:
            data = pd.read_csv(input_, header=list(index_col), index_col=0,
                               parse_dates=True)
            yield data
        except Exception as e:
            click.echo('Could not input file "%s": %s' % (input_, e), err=True)


# making transforma functions
transforms = [chi2normal_transformation, percentile_score, dropna,
              resample_return, columns_selector, stdout]

for transform in transforms:
    g = apply(transform)
    data_pipeline.command()(g)

@data_pipeline.command("count_na")
@apply
def count_na(data):
    click.echo(data.isna().sum())


@data_pipeline.command()
@click.option("-o", "--output", "output", type=click.File("w"))
@apply
def dump(data, output):
    content = data.to_csv()
    output.writelines(content)


@data_pipeline.resultcallback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    ""[summary]
    """
    # Start with an empty iterable.
    stream = ()
    # Pipe it through all stream processors.
    for processor in processors:
        if processor is not None:
            stream = processor(stream)

    if isinstance(stream, types.GeneratorType):
        for pipe in stream:
            pass


if __name__ == "__main__":
    data_pipeline(prog_name="data-pipline")
