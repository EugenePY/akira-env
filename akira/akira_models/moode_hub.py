import os
import faust
from arctic import Arctic
from arctic.date import DateRange
from typing import Mapping

import datetime

app = faust.App("model-hub",
                borker=f"kafka: // {os.environ.get('KAFKA_BOOSTRAPHOST',
                                                   'localhost:9092')}")

data_spec = {
    "bmk": {"symbols": ["USDKRW INVT Curncy", "USDTWD INVT Curncy",
                        "USDSGD INVT Curncy", "AUDUSD INVT Curncy",
                        "GBPUSD INVT Curncy"]},

    "mv": {"symbols": ["USDKRW INVT Curncy", "USDTWD INVT Curncy",
                       "USDSGD INVT Curncy", "AUDUSD INVT Curncy",
                       "GBPUSD INVT Curncy"]}
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

model_table = app.SetTable("model-table")  # trained model obj


class TradingModel(faust.Record):
    mode_id: str
    model_obj: str
    model_spec: Mapping[str, str] = None
    data_spec: Mapping[str, str] = None
    last_update: datetime.datetime

    async def load_model(self):
        return pkl.loads(self.model_obj)


class ModelInference(faust.Record):
    mode_id: str
    data: Mapping = None
    func_kwarg: Mapping[str, str] = {}


@app.agent(model_submit)
async def submit_model(trading_model) -> None:
    """A "worker" stream processor that executes tasks."""
    async for model in tradin_model:
        pass


async def train_model(model, data, **kwargs):
    model.fit(data, **kwargs)
    # Transform the data points
    return model


async def predict_model(model, input, **params):
    '''using trained model obj to predict'''
    return prediction


async def update_basekets(model_id, start, end):
    from akira.akira_models.basket.utils import get_model
    # updating model
    store = Arctic(os.environ.get("MONGODB_URI",
                                  "localhost:27017"))
    lib = store.get_library("akira.tickers")
    spec = data_spec[model_id]
    cols = {}
    for symbol in spec["symbols"]:
        cols[symbol] = lib.read(
            symbol, date_range=DateRange(
                start=start, end=end))

    data = pd.concat(cols, axis=1)
    model_cls_spec = model_spec[model_id]
    model = get_model(model_id)(**model_cls_spec)
    model.fit(data)
    # submit trades
    return model


@app.task
async def initial_models():
    start = datetime.datetime(2020, 1, 1)
    end = datetime.datetime.today() - datetime.timedelta(days=1)

    model = await update_basekets("bmk", start, end)

    await model_submit.send(value=TradingModel(
        model_id="bmk", model_obj=pkl.dumps(model),
        model_spec=model_spec["bmk"],
        data_spec=data_spec["bmk"],
        last_update=datetime.datetime.now()))


@app.agent(model_trade_submit)
async def submit_order(order_stream):
    async for model_input in order_stream:
        current_model = model_table[model_id].current()
        order = current_model.predict(model_input.data)
        yield order


@app.interval(10)  # submit trades
async def submit_orders():
    model_id = "bmk"
    data = data_spec[model_id]
    spec = data_spec[model_id]
    start = datetime.datetime.today()
    end = start - datetime.timedelta(days=1)

    cols = {}
    for symbol in spec["symbols"]:
        cols[symbol] = lib.read(
            symbol, date_range=DateRange(
                start=start, end=end))
    data = pd.concat(cols, axis=1)
    await submit_order.map(value=ModelInput(model_id=model_id,
                                            data=data))


if __name__ == "__main__":
    app.
