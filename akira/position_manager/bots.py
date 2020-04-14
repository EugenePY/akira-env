
import abc
import ssl
import sys
import uuid

import aiohttp
import faust
import numpy as np
from twisted.python import log
import ssl
import asyncio
from akira_data.data.ws.investdot.asyncio_temp import InvestingdotcomProtocol
from autobahn.asyncio.websocket import WebSocketClientFactory
from collections import defaultdict
from loguru import logger
from akira.position_manager.models import ExecutedPrice
logger.remove()
logger.add(sys.stderr, level="INFO")


class Agent(object):

    @abc.abstractmethod
    def act(self, obs):
        pass


class BaselineExecAgent(InvestingdotcomProtocol, Agent):
    _position = 0
    _means = defaultdict(lambda: 0)
    _counts = defaultdict(lambda: 0)
    _stacks = defaultdict(list)
    _sp_stack = defaultdict(list) 

    execute_px = None

    def act(self, obs):
        id_ = obs["pid"]
        mean = self._means[id_]
        counts = self._counts[id_]
        px = (float(obs["bid"]) + float(obs["ask"]))/2
        sp =(float(obs["bid"]) - float(obs["ask"]))
        alpha = counts/(1+counts)
        self._means[id_] += (1 - alpha) * (px - mean)
        self._counts[id_] += 1
        self._stacks[id_].append(px)

    def onMessage(self, msg, binary):
        data = super().onMessage(msg, binary)
        if data is not None:
            action = self.act(obs=data)

    def onClose(self, wasClean, code, reason):
        print(f"WebSocket connection closed: {reason}, code={code}")
        executed_px = []
        for symbol in self._means.keys():
            out = ExecutedPrice(
                symbol=symbol, window_start=int(self.start), 
                window_end=int(self.start + self.timeout),
                execute_px=self._means[symbol],
                median=np.median(self._stacks[symbol]),
                std=np.std(self._stacks[symbol]),
                avg_spread=np.mean(self._sp_stack[symbol]),
                tick_count=self._counts[symbol],
                method="MEAN")
            executed_px.append(out)
        self.execute_px = executed_px


def run_agent(ids, interval):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    numb = np.random.randint(0, 1000)
    server_num = np.random.randint(0, 200)
    randstr = str(uuid.uuid1())[:8]
    url = f"wss://stream{server_num}.forexpros.com/echo/{numb}/{randstr}/websocket"
    host = f"stream{server_num}.forexpros.com"

    factory = WebSocketClientFactory(url)
    factory.setProtocolOptions(autoPingInterval=1)
    factory.protocol = BaselineExecAgent.make_subids(ids).set_timeout(interval)
    return factory, host, 445, ctx


if __name__ == "__main__":
    app.main()
