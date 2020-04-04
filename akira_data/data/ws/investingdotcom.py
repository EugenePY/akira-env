import asyncio
import json
import time
import uuid

import kafka
import numpy as np
from autobahn.twisted.websocket import (WebSocketClientFactory,
                                        WebSocketClientProtocol, connectWS)
from kafka import KafkaProducer
from loguru import logger
import datetime


def output_producer(f):
    def onMessage(self, *arg, **kwargs):
        out = f(self, *arg, **kwargs)
        if out is not None:
            out = {"symbol": f"FEED:pid-{out['pid']}",
                   "data": out, "index": datetime.datetime.utcfromtimestamp(
                       out["timestamp"])}
            self.producer.send(self.topic, out)
            logger.debug(f"Kafka-producer:topic={self.topic}:{out}")
        return out
    return onMessage


class InvestingdotcomProtocol(WebSocketClientProtocol):
    """
        var k = {
            protocols_whitelist: ["websocket", "xdr-streaming", "xhr-streaming", "iframe-eventsource", "xdr-polling", "xhr-polling"],
            debug: !0,
            jsessionid: !1,
            server_heartbeat_interval: 5e3,
            heartbeatTimeout: 5e3
        };
        p = !1,
        o = new SockJS(window.stream + "/echo",null,k);
    """

    heartbeat = {"_event": "heartbeat", "data": "h"}
    subscribte_message = {"_event": "bulk-subscribe", "tzID": "8",
                          "message": "pid-1:%%pid-2:"}

    @classmethod
    def make_subids(cls, ids):
        cls.subscribte_message.update({"message": "%%".join(
            [f"pid-{id_}:" for id_ in ids])})
        return cls

    @classmethod
    def produce_to_kafka(cls, topic, max_retry=2, retry_time=2, *arg, **kwarg):
        retry = 0
        connected = False
        if max_retry == -1:
            max_retry = np.inf

        while not connected:
            try:
                cls.producer = KafkaProducer(
                    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                    *arg, **kwarg)
                connected = True
            except kafka.errors.NoBrokersAvailable:
                logger.info("Retry connecting Kafka")
                time.sleep(retry_time)
                retry += 1
            if retry >= max_retry:
                raise kafka.errors.NoBrokersAvailable

        cls.topic = topic
        connect = False
        logger.info(f"Wait for KafKa={kwarg['bootstrap_servers']}")
        while not connect:
            connect = cls.producer.bootstrap_connected()
        logger.info("Kafka-Connected")
        return cls

    def onConnect(self, request):
        logger.info("Client connecting: {}".format(request.peer))

    def sendMessage(self, dict_):
        out = json.dumps(json.dumps(
            dict_)).encode('utf-8')
        super().sendMessage(out, isBinary=False)
        return out

    def onOpen(self):
        logger.info("WebSocket connection open.")
        self.sendMessage(self.subscribte_message)
        self.pingsReceived = 0
        self.pongsSent = 0

    @output_producer
    def onMessage(self, msg, binary):
        msg = str(msg.decode("utf-8"))[1:]
        if len(msg) > 0:
            obj = json.loads(msg)
            data = json.loads(obj[0]).get('message', None)

            if data is not None:
                result = json.loads(data.split('::')[1])
                logger.debug(f"receive:{result}")
                return result

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {}".format(reason))

    def onPing(self, payload):
        self.pingsReceived += 1
        logger.debug("Ping received from {} - {}".format(
            self.peer, self.pingsReceived))
        self.sendPong(payload)
        self.pongsSent += 1

    def onPong(self, payload):
        self.sendMessage(self.heartbeat)
        logger.debug("Pong sent to {} - {}".format(
            self.peer, self.pongsSent))


if __name__ == "__main__":
    def test():
        import sys
        import ssl
        from twisted.python import log
        from twisted.internet import reactor, ssl
        import numpy as np

        log.startLogging(sys.stdout)
        numb = np.random.randint(0, 1000)
        server_num = np.random.randint(0, 200)
        randstr = str(uuid.uuid1())[:8]
        url = f"wss://stream{server_num}.forexpros.com/echo/{numb}/{randstr}/websocket"
        factory = WebSocketClientFactory(url)   # , #headers=headers)
        factory.setProtocolOptions(autoPingInterval=1)
        factory.protocol = InvestingdotcomProtocol
        connectWS(factory)
        reactor.run()
    test()
