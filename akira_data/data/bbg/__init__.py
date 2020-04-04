import json
from functools import reduce

import numpy as np
import pandas as pd
import requests
from akira_data.data.base import API

import io


class BBGapiClient(API):
    """
    Bloomberg API wrapper
    """
    name = "bbg"

    def __init__(self, host={"ip": "http://10.87.32.215",
                             "port": "168"}, debug_mode=False):
        self.host = host

        self._debug_mode = debug_mode
        if self._debug_mode:
            self.bdh = self._bdh_debug

    def get(self, symbol, fields, start, end):
        return self.bdh(symbol, fields, start.strftime("%Y%m%d"), 
            end.strftime("%Y%m%d"))

    def get_batch(self, symbols, fields, start, end):
        start, end = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
        return self.bdh(symbols, fields, start, end)

    def _bdh_debug(self, tickers, fields, start, end):
        if isinstance(fields, list):
            fields = list(fields)
        elif isinstance(tickers, list):
            tickers = list(tickers)

        date = pd.date_range(start, end)
        n_col = len(tickers) * len(fields)
        values = np.random.normal(size=(len(date), n_col))
        out = pd.DataFrame(values, columns=pd.MultiIndex.from_product(
            [tickers, fields]), index=date)
        return out

    def bdh(self, tickers, fields, start, end):
        function_input = {"tickers": tickers,
                          "fields": fields,
                          "start": start,
                          "end": end}

        host = self.host
        req = requests.post(
            "{ip}:{port}{route}".format(
                route="/api/pdblp/bdh",
                **host),
            json=function_input)

        if req.status_code == 400:
            raise ConnectionError("Cannot find corresponding"
                                  " ip={ip}, port={port}: res={res}".format(
                                      **host, res=req.text))

        if req.status_code == 403:
            raise ConnectionError("Block by host")

        elif req.status_code == 404:
            raise ConnectionError("Cannnot reach BBG API")

        data = json.loads(req.text)
        if data["status"] != "success":
            raise RuntimeError(data["status"])
        df = pd.read_csv(io.StringIO(
            data["data"]), index_col=[0], header=[0, 1])
        df.index = pd.DatetimeIndex(df.index)
        return df

    def dict_tickers(self, dict_tickers, fields, start, end):
        """
        additional faster interface for {"keys": ["ticker0", "ticker1", ...]}
        """
        ticker_all = list(
            set(reduce(lambda x, y: x+y, dict_tickers.values())))
        df = self.bdh(ticker_all, fields, start, end)
        dfs = {k: df[v] for k, v in dict_tickers.items()}
        return dfs
