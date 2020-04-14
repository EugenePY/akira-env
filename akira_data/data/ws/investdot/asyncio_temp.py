import json
import time
import uuid

import kafka
import numpy as np
from autobahn.asyncio.websocket import (WebSocketClientProtocol,
                                        WebSocketClientFactory)

from loguru import logger
import datetime


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
    timeout = None

    @classmethod
    def make_subids(cls, ids):
        cls.subscribte_message.update({"message": "%%".join(
            [f"pid-{id_}:" for id_ in ids])})
        return cls

    @classmethod
    def set_timeout(cls, timestamp):
        cls.timeout = timestamp
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
        self.start = int(time.time())

    def onMessage(self, msg, binary):
        logger.debug(
            "WebSocketProtocol.onMessage(payload=<{payload_len} bytes)>, isBinary={isBinary}",
            payload_len=(len(msg) if msg else 0),
            isBinary=binary,
        )
        msg = str(msg.decode("utf-8"))[1:]
        if len(msg) > 0:

            logger.debug(f"receive:{msg}")
            obj = json.loads(msg)

            data = json.loads(str(obj[0]))
            if data == 3000:
                self.onClose(wasClean=False,
                             code=obj[0], reason=obj[1])
            else:
                data = data.get("message", None)

                if data is not None:
                    result = json.loads(data.split('::')[1])
                    logger.info(result)
                    return result

        if self.timeout is not None:
            if self.timeout < int(time.time()) - self.start:
                self.log.info("Timeout closing connection by User")
                self.sendClose()

    def onClose(self, wasClean, code, reason):
        logger.info(f"WebSocket connection closed: {reason}, code={code}")

    def onPing(self, payload):
        if not self.is_closed:
            self.pingsReceived += 1
            logger.debug("Ping received from {} - {}".format(
                self.peer, self.pingsReceived))
            self.sendPong(payload)
            self.pongsSent += 1

    def onPong(self, payload):
        if not self.is_closed:
            self.sendMessage(self.heartbeat)
            logger.debug("Pong sent to {} - {}".format(
                self.peer, self.pongsSent))


if __name__ == "__main__":
    def testing_main():
        import asyncio
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        numb = np.random.randint(0, 1000)
        server_num = np.random.randint(0, 200)
        randstr = str(uuid.uuid1())[:8]
        url = f"wss://stream{server_num}.forexpros.com/echo/{numb}/{randstr}/websocket"
        host = f"stream{server_num}.forexpros.com"

        factory = WebSocketClientFactory(url)
        factory.setProtocolOptions(autoPingInterval=5)
        factory.protocol = InvestingdotcomProtocol.make_subids([1, 2])

        loop = asyncio.get_event_loop()
        # {"cert_reqs": ssl.CERT_NONE})
        coro = loop.create_connection(factory, host, 443, ssl=ctx)
        loop.run_until_complete(coro)
        loop.run_forever()
        # loop.close()
    #testing_main()
