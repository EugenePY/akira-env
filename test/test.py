import pytest
import faust
from akira_env.envs.simple_env import SimpleGuessingEnv
import pandas as pd
from kafka import KafkaProducer
import datetime
import numpy as np
import json
import logging
log = logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="module")
def testing_data():
    start = datetime.datetime(2020, 1, 1)

    with open("test/data/15m-fx-rate.csv", "r") as f:
        intraday = pd.read_csv(f, index_col=[0, 1], parse_dates=[1])
        selected_idx = intraday.index[intraday.index.get_level_values(
            1) > start]
        intraday = intraday.loc[selected_idx]

    with open("test/data/daily-fx.csv", "r") as f:
        fx_rate = pd.read_csv(f, index_col=[0, 1], parse_dates=[1])
        selected_idx = fx_rate.index[fx_rate.index.get_level_values(1) > start]
        fx_rate = fx_rate.loc[selected_idx]

    with open("test/data/eco-events.csv", "r") as f:
        eco_event = pd.read_csv(f, index_col=[0, 'time'], parse_dates=["time"])
        eco_event = eco_event.loc[eco_event.index.get_level_values(1) > start]

    return {"daily-fx": fx_rate, "intray": intraday, "eco-event": eco_event}


def test_inject_data2kafka(testing_data):
    # DataProducer
    hostname = "localhost"
    producer = KafkaProducer(
        bootstrap_servers=[f"{hostname}:9092"],
        key_serializer=lambda x: x.encode("utf-8"),
        value_serializer=lambda x: x.encode("utf-8"))

    for name, v in testing_data.items():
        v.index.names = ["symbol", "date"]
        v = v.reset_index()
        # idx = v.index.levels[1]
        for entry in v.iterrows():
            # entry = v.loc[(slice(None), i), :].loc[]
            # raise
            # print(name)
            producer.send("trading_indexing_by_timestamp", key=entry[1]["symbol"], value=entry[1].to_json(),
                          timestamp_ms=int(entry[1].date.timestamp()*1000))
    producer.flush()


@pytest.fixture(scope="module")
def ksql_conn():
    import logging
    from ksql import KSQLAPI
    client = KSQLAPI('http://localhost:8088')
    print(client.ksql('SHOW TABLES;\nSHOW TOPICS;\nSHOW STREAMS;'))
    return client


def test_create_table(ksql_conn):
    # Not materilized
    table_name = "daily_fx"
    topic = 'trading'
    value_format = 'JSON'
    columns_type = ['symbol VARCHAR', "date BIGINT", 'PX_LAST DOUBLE',
                    "PX_OPEN DOUBLE", "PX_LOW DOUBLE", "PX_HIGH DOUBLE"]
    res = ksql_conn.create_table(table_name=table_name,
                                 columns_type=columns_type,
                                 topic=topic,
                                 value_format=value_format,
                                 key=["symbol", "date"])


def test_create_stream(ksql_conn):
    # Not materilized
    table_name = "daily_fx_stream"
    topic = 'trading'
    value_format = 'JSON'
    columns_type = ['symbol VARCHAR', "date BIGINT", 'PX_LAST DOUBLE',
                    "PX_OPEN DOUBLE", "PX_LOW DOUBLE", "PX_HIGH DOUBLE"]
    res = ksql_conn.create_stream(table_name=table_name,
                                  columns_type=columns_type,
                                  topic=topic,
                                  value_format=value_format)


def test_selected_stream(ksql_conn):
    ksql = """CREATE STREAM eurusd_daily_rate AS
    SELECT * FROM daily_fx_stream
    WHERE symbol='EURUSD INVT Curncy'
    EMIT CHANGES;"""
    res = ksql_conn.ksql(ksql)
    print(res)
    raise


def test_query_tables(ksql_conn):
    stream = ksql_conn.query("SELECT * FROM DAILY_FX EMIT CHANGES;")
    for item in stream:
        print(item)
        raise


def test_topic(ksql_conn):
    query = ksql_conn.query("PRINT trading FROM BEGINNING LIMIT 5;")
    for item in query:
        print(item)


def test_stream(ksql_conn):
    start = datetime.datetime(2018, 1, 1)
    end = datetime.datetime(2018, 5, 5)

    # query = ksql_conn.query(
    #    f"SELECT * FROM eurusd BETWEEN {int(start.timestamp()*1000)} AND {int(end.timestamp()*1000)};")
    query = ksql_conn.query("PRINT EURUSD")

    for item in query:
        print(item)

    # for item in query:
    #    print(item)
    raise
