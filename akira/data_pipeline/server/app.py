'''
For static data, we first
'''
import faust
import arctic

from arctic import Arctic, TICK_STORE, VERSION_STORE
from arctic.store.metadata_store import METADATA_STORE_TYPE
import os
import datetime
from datetime import timezone
from dateutil.parser import parse as parse_date
from pandas.tseries.offsets import BDay
from typing import Mapping, Any
from arctic.date import mktz
from mode.utils.logging import get_logger
import pandas as pd
import time
from tzlocal import get_localzone
from akira.position_manager.execution import Tick, ticker_topic
logger = get_logger(__name__)

app = faust.App('akira-data',
                broker=f"kafka://{os.environ.get('KAFKA_BOOSTRAPHOST', 'localhost:9092')}")

store = Arctic(os.environ.get("MONGODB_URI", "localhost:27017"))
store.initialize_library("akira.tickers", lib_type=TICK_STORE)
store.initialize_library("akira.metadata", lib_type=METADATA_STORE_TYPE)

ticker_lib = store["akira.tickers"]


def tz_parser(*args, default_tzinfo=get_localzone(), **kwargs):
    dt = parse_date(*args, **kwargs)
    return dt.replace(tzinfo=dt.tzinfo or default_tzinfo)


class Ticker(faust.Record, coerce=True, date_parser=tz_parser):
    symbol: str
    data: Mapping[str, Any]
    index: datetime.datetime
    metadata: Mapping = None


tickdata_topic = app.topic(
    os.environ.get("INVESTINGDOT_COM_TOPIC", "investing-dot-topic"), 
    value_type=Ticker)  # ticker data only


async def forward_to_execute_tick(ticker):
    # forward excution data to tick data topic
    if "FEED" in ticker.symbol:
        tick = Tick(timestamp=int(ticker.index.timestamp()),
                    ask=float(ticker.data["ask"]),
                    bid=float(ticker.data["bid"]),
                    symbol=ticker.symbol)
        logger.info(f"fowrad to ticker topic={tick}")
        await ticker_topic.send(key=ticker.symbol, value=tick)


@app.agent(tickdata_topic)
async def proccess_tick_data(tickdata):
    # ticker store
    async for tick in tickdata.group_by(Ticker.symbol):
        logger.info(f"ticker-proccess got: {tick.asdict()}")
        data = tick.data
        data["index"] = tick.index.replace(tzinfo=get_localzone())
        ticker_lib.write(tick.symbol, [data])

        if tick.metadata is not None:
            logger.info(f"metadata-proccess got: {metadata.asdict()}")
            lib = store["akira.metadata"]
            lib.append(tick.symbol, tick.metadata,
                       start_time=tick.index.replace(tzinfo=get_localzone()))


        # foward FEED data to tick proccess
        await forward_to_execute_tick(tick)
        yield tick


class DataTask(faust.Record, coerce=True, date_parser=tz_parser):
    symbol: str
    api_id: str
    start: datetime.datetime
    end: datetime.datetime


task_topic = app.topic('data-task', value_type=DataTask)
api_status_topic = app.topic('api-status-task', value_type=DataTask)
api_call_topic = app.topic('api-call-task', value_type=DataTask)
api_map = {}


@app.agent(task_topic)
async def create_data_task(tasks):
    async for task in tasks:
        await calculated_difference.send(value=task)


@app.agent(api_call_topic, concurrency=10)
async def do_api_call_task(task_stream):
    async for task in task_stream:
        logger.info(f"received batch-ticker-job={task}")
        api = api_map.get(task.api_id, None)

        if api is not None:
            data = api.get(
                task.symbol, start=task.start.replace(tzinfo=None),
                end=task.end.replace(tzinfo=None))

            if isinstance(data, pd.DataFrame):
                data.index = pd.DatetimeIndex(
                    [t.tz_localize("UTC") for t in data.index])
                data = data.reset_index().to_dict("record")
            try:
                ticker_lib.write(task.symbol, data)
                yield task

            except arctic.exceptions.OverlappingDataException as e:
                print(e)

        else:
            print(f"api={task.api_id} not exists.")


@app.agent(api_status_topic)
async def calculated_difference(tasks):
    async for task in tasks:
        lib = ticker_lib
        try:
            task.end = max(lib.max_date(
                           task.symbol), task.end)
            task.start = lib.max_date(task.symbol)
            print(task)
        except arctic.exceptions.NoDataFoundException as e:
            print(e)
        await do_api_call_task.send(value=task)


@app.task
async def on_start():
    from akira_data.data.web.pool import \
        (EcoEventVariablePool, IntraDayVariablePool, InvestingDotVariablePool)
    from akira_data.data.bbg.pool import SpotUniverse, REER
    #os.environ.get("POOLS", "ECO, INTRADAY")
    # IntraDayVariablePool]  # SpotUniverse, REER]
    pools = [EcoEventVariablePool, IntraDayVariablePool,
             InvestingDotVariablePool]
    start = datetime.datetime(2020, 1, 1)
    end = datetime.datetime.today()

    for pool in pools:
        pool_id = pool.__name__.lower()
        api_map[pool_id] = pool()
        logger.info(f"Loading Variable Pools={pool_id}")

    for pool_id in api_map.keys():
        for variable in api_map[pool_id].variables.values():
            task = DataTask(
                symbol=variable.symbol,
                api_id=pool_id, start=start, end=end)
            await create_data_task.send(value=task)


@app.crontab('0 20 * * *')  # batch job
async def every_day_at_8_pm():
    # maping ticker data into chunk data
    # update all pool
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=7)

    for pool in pools:
        for variable in api_map[pool_id].variables.values():
            task = DataTask(symbol=variable.symbol,
                            api_id=pool_id, start=start, end=end)
            await create_data_task.send(value=task)


if __name__ == '__main__':
    app.main()
