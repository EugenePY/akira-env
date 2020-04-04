# -*- coding: utf-8 -*-

import click
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2
import dill as pkl
import yaml
import sys
import os


def get_model(model_id):
    if model_id == "bmk":
        from baskets.src.passive_model import BasketModel
        return BasketModel

    elif model_id == "factor":
        from baskets.src.passive_model import FactorDynamicBasketModel
        return FactorDynamicBasketModel

    elif model_id == "tvols":
        from baskets.src.passive_model import TVOLS
        return TVOLS

    elif model_id == "mv":
        from baskets.src.passive_model import MinimizeVolatilityModel
        return MinimizeVolatilityModel
    else:
        raise ValueError(f"model_id={model_id} not Found.")


@click.pass_context
def model_task(ctx):
    '''Basket Model commandline interface'''
    # calculate monthly returns
    ctx.obj = {}


@model_task.command()
@click.option('-s', "--spec", "spec", type=click.File("r"), help="spec file, .yaml")
@click.option('-m', '--model_id', 'model_id',
              type=click.Choice(
                  ["bmk", "mv", "factor", "tvols"],
                  case_sensitive=False),
              help='choose model_id')
@click.pass_context
def make_model(ctx, spec, model_id):
    '''create model obj
    '''
    model_cls = get_model(model_id)

    input_yaml = yaml.load(spec, Loader=yaml.FullLoader)
    spec = input_yaml["model_spec"]
    model = model_cls(**spec)
    click.echo(f"model={model}")
    ctx.obj["model"] = model
    ctx.obj["spec"] = input_yaml


@model_task.command()
@click.option('-i', '--input', 'input',
              type=click.File('r'), help='model-training input: .csv')
@click.option('-o', '--output', 'output',
              type=click.File('wb'), help='model-training output: pkl.fmt')
@click.pass_context
def train(ctx, input, output):
    ''' training the model: generate model obj file '''
    data = pd.read_csv(input, index_col=[0], header=[0, 1])

    model = ctx.obj.get("model", None)

    if model is None:
        raise ValueError("pls spec your model first.")

    spec = ctx.obj["spec"]["train"]
    model.fit(data, **spec)
    # Transform the data points
    pkl.dump(model, output)


@model_task.command()
@click.option('-m', '--model_file', 'model', type=click.File('rb'),
              help='trained model obj file, pkl fmt')
@click.option('-i', '--input', 'input', type=click.File('rb'),
              help='input-data file, .csv')
@click.option('-o', '--output', 'output', type=click.File('w'),
              help='model_predict output: .csv')
@click.pass_context
def predict(ctx, model, input, output):
    '''using trained model obj to predict'''
    model = pkl.load(model)
    test_data = pd.read_csv(input, index_col=[0], header=[0, 1])
    spec = ctx.obj["spec"]["predict"]
    if spec is None:
        spec = {}
    prediction = model.predict(test_data, **spec)
    output.writelines(prediction.to_csv())


if __name__ == "__main__":
    model_task(prog_name="model-task")
