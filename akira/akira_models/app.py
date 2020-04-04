import os
import faust
from faust.cli import option
import click
import arctic
import typing
from functools import wraps
import pandas as pd
#from akira_env.position_manager import order_topic, Order
from mode.utils.objects import qualname
import yaml
import pickle as pkl

app = faust.App("baskets", reply_to="akira_env.trading-log",
                borker=f"kafka://{os.environ.get('KAFKA_BOOSTRAPHOST', 'localhost:9092')}")

data_spec = {
    "bmk": {"symbols": ["USDKRW INVT Curncy", "USDTWD INVT Curncy",
                        "USDSGD INVT Curncy", "AUDUSD INVT Curncy",
                        "GBPUSD INVT Curncy"]},

    "mv": {"symbols": ["USDKRW INVT Curncy", "USDTWD INVT Curncy", "USDSGD INVT Curncy",
                       "AUDUSD INVT Curncy", "GBPUSD INVT Curncy"]}
}


model_spec = {
    "bmk": {"target": "USDTWD INVT Curncy",
            "portfolio": ["USDKRW INVT Curncy",
                          "USDSGD INVT Curncy",
                          "AUDUSD INVT Curncy",
                          "GBPUSD INVT Curncy"]},
    "mv": {"p": 1, "q": 1, "VAR_lag": 1, "model": "dcc"},
    "tvols": {"bandwidth": 0.1, "kernel": "gaussian"}
}


class Ticker(faust.Record, coerce=True, date_parser=tz_parser):
    symbol: str
    data: Mapping[str, Any]
    index: datetime.datetime


# externel topic
data_topic = app.topic("ticker-topic", value_type=Ticker)


class Requests(faust.Record):
    id: str
    model_id: str
    name: str
    args: typing.Sequence
    kwargs_: typing.Mapping

    async def __call__(self) -> typing.Any:
        return await self.handler(*self.args,
                                  **self.kwargs_)

    @property
    def handler(self) -> typing.Callable[..., typing.Awaitable]:
        return task_registry[self.task]


model_task_topic = app.topic("model-task-topic", value_type=Requests)
task_registry = {}


class ModelSpace(faust.Record):
    model_obj: str
    model_spec: Mapping
    __last_update: datetime.datetime = datetime.datetime.now()

    @property
    def last_update(self):
        return self.__last_update

    def update(self, data):
        for key in ["model_obj", "model_spec"]:
            getattr(self, key) = data[key]


model_table = app.Table("model-deploy-table", default_value=ModelSpace)


@app.agent(model_task_topic)
async def process_task(tasks) -> None:
    """A "worker" stream processor that executes tasks."""
    async for task in tasks.groupby(Requests.model_id):
        print(f'Processing task: {task!r}')
        result = await task()
        print(f'Result of {task.id} is: {result!r}')

        if task.name == "submit":
            model_state = model_table[task.model_id]


class Task:

    def __init__(self, fun, *, name=None) -> None:
        self.fun = fun
        self.name = name or qualname(fun)

    def __call__(self, *args, **kwargs):
        return self.fun(*args, **kwargs)

    async def delay(self, *args, **kwargs):
        return await self.apply_async(args, kwargs)

    async def apply_async(self,
                          args,
                          kwargs,
                          id: str = None,
                          **options):
        id = id or faust.uuid()
        return await process_task.send(value=Request(
            id=id,
            name=self.name,
            arguments=args,
            keyword_arguments=kwargs,
        ))


def task(fun) -> Task:
    # Task decorator
    task = Task(fun)
    task_registry[task.name] = task
    return task


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


@task
async def train_model(model, data, **kwargs):
    model.fit(data, **kwargs)
    # Transform the data points
    return model


@task
async def predict_model(model, input, **params):
    '''using trained model obj to predict'''
    prediction = model.predict(test, **params)
    return prediction


@app.command(
    option('-m', '--model_id', 'model_id',
           type=click.Choice(
               ["bmk", "mv", "factor", "tvols"],
               case_sensitive=False),
           help='choose model_id'),
    option('-i', '--input', 'input',
           type=click.File('r'), help='model-training input: .csv'),
    option('-o', '--output', 'output',
           type=click.File('wb'), help='model-training output: pkl.fmt'),
    option('-s', "--spec-file", "spec",
           type=click.File("r"), help="spec file, .yaml"),
)
async def train(self, model_id, input, output, spec):
    '''create model obj
    '''
    if spec is not None:
        input_yaml = yaml.load(spec, Loader=yaml.FullLoader)
        spec = input_yaml["model_spec"]
        # override the existing, parameters

    model_cls = get_model(model_id)

    model = model_cls(**spec)
    click.echo(f"model={model}")

    data = pd.read_csv(input, index_col=[0], header=[0, 1])
    model = await train_model(model, data, **input_yaml)

    # Transform the data points
    pkl.dump(model, output)


@app.command(
    option('-m', '--model_id', 'model_id',
           type=click.Choice(
               ["bmk", "mv", "factor", "tvols"],
               case_sensitive=False),
           help='choose model_id'),
    option('-l', "--model-file", "model_file",
           type=click.File("rb"), help="model obj file, pkl"),
    option('-s', "--spec-file", "spec",
           type=click.File("r"), help="spec file, .yaml")
)
async def deploy_model(self, model_id, model_file, model_spec):
    '''create model obj
    '''
    if spec is not None:
        input_yaml = yaml.load(model_spec, Loader=yaml.FullLoader)
        spec = input_yaml["model_spec"]
        # override the existing, parameters


@app.command(
    option('-m', '--model_file', 'model', type=click.File('rb'),
           help='trained model obj file, pkl fmt'),
    option('-i', '--input', 'input', type=click.File('rb'),
           help='input-data file, .csv'),
    option('-o', '--output', 'output', type=click.File('w'),
           help='model_predict output: .csv')
)
async def predict(self, model, input, output, spec):
    '''using trained model obj to predict'''
    model = pkl.load(model)
    test_data = pd.read_csv(input, index_col=[0], header=[0, 1])
    spec = ctx.obj["spec"]["predict"]
    if spec is None:
        spec = {}
    prediction = model.predict(test_data, **spec)
    output.writelines(prediction.to_csv())


@app.command(
    option('-s', '--start', 'start',
           help='trained model obj file, pkl fmt'),
    option('-e', '--end', 'end',
           help='input-data file, .csv'),
)
async def backtesting(self, start, end):
    '''using trained model obj to predict'''
    pass


if __name__ == "__main__":
    app.main()
