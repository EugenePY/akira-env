import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib
import time
import abc
from collections import defaultdict
from akira_data.db.events import EcoEventSchema, CountryCode
import asyncio
import datetime
import json
from loguru import logger
#import nest_asyncio
from akira_data.data.base import API
import pandas as pd
from pandas.tseries.offsets import BDay
from arctic.date import mktz

# nest_asyncio.apply()


class EcoEventAPI(API):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"}

    schema = EcoEventSchema

    def get_all_country_code(self):
        req = requests.get("https://www.investing.com/economic-calendar/", "html",
                           headers=self.default_headers)
        dom = BeautifulSoup(req.text, "html.parser")
        all_country = dom.find("ul", {"class": "countryOption"}).find_all("li")
        contry_list = {}
        for li in all_country:
            conury_name = li.find('label').text
            contry_list[conury_name] = li.find("input")["value"]

        self.contry_dict = contry_list
        return contry_list

    def get(self, sess, country, start, end):
        event_list = []
        for event in self.eco_event_loop(sess, country, start, end):
            event_list.append(event)
        return self.schema(many=True).dump(event_list)

    def eco_event_loop(self, country, start, end):
        with requests.session() as sess:
            batch = 0
            Ms = [start, end]
            while True:
                # it required to bathc query for investing.com api
                query = self.get_economic_calender(
                    sess,
                    [CountryCode(country).value], [
                        Ms[0], Ms[1]],
                    mkr_volatility=["1", "2", "3"], batch=batch)

                all_events = query["pids"]
                soup = BeautifulSoup(query["data"],
                                     features="lxml")

                logger.info("{}, Got {} of events...".format(
                    CountryCode(country).name,
                    len(all_events)))

                for event in all_events:
                    event = event.replace("event-", "").replace(":", "")
                    event_soup = soup.find(
                        "tr", {"id": "eventRowId_{}".format(event)})

                    # geting the eco event
                    eco_event = self.schema().from_investing_data(
                        event_soup)
                    eco_event = self.schema().dump(eco_event)

                    eco_event["index"] = pd.to_datetime(
                        eco_event["index"]).replace(tzinfo=mktz("UTC+8"))
                    yield eco_event

                if len(all_events) != 0:
                    batch += 1
                else:
                    break

    def get_batch(self, contrys, start, end):
        from concurrent.futures import ThreadPoolExecutor
        missions = {}
        for i in contrys:
            missions[i] = False

        async def async_crawl():
            with ThreadPoolExecutor(max_workers=10) as executor:
                with requests.Session() as sess:
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(
                            executor, self.get,
                            *(sess, k, start, end))
                        for k, v in missions.items()
                    ]
                    for response in await asyncio.gather(*tasks):
                        pass
            return tasks

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(async_crawl())
        loop.run_until_complete(future)
        data = {contrys[i]: v.result() for i, v in enumerate(future.result())}
        return data

    @staticmethod
    def get_economic_calender(sess, contrys, dates, mkr_volatility, batch):
        # TODO: make this cleaner
        date_start = dates[0].strftime("%Y-%m-%d")
        date_end = dates[1].strftime("%Y-%m-%d")
        form_data = {"dateFrom": date_start, "dateTo": date_end, "timeZone": 86,
                     "timeFilter": "timeRemain", "limit_from": 0}

        for contry_key in contrys:
            form_data["country[]"] = contry_key

        form_data["importance[]"] = mkr_volatility
        form_data["limit_from"] = batch
        data = sess.post("https://www.investing.com/economic-calendar/Service/getCalendarFilteredData",
                         data=form_data,
                         headers={
                             "Accept": "*/*",
                             "Accept-Encoding": "gzip, deflate, br",
                             "Accept-Language": "en-US,en;q=0.9",
                             "Connection": "keep-alive",
                             "Content-Length": "421",
                             "Content-Type": "application/x-www-form-urlencoded",
                             "DNT": "1",
                             "Host": "www.investing.com",
                             "Origin": "https://www.investing.com",
                             "Referer": "https://www.investing.com/economic-calendar/",
                             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                             "X-Requested-With": "XMLHttpRequest"}
                         ).json()
        return data


class InvestingDotComAPI(API):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"}

    def __init__(self):
        # NOTE: limit 200 datapoint per request for economics calender
        self.zombie_info = self.get_zombie_info()

    def get(self, asset_id, start, end, resolution):
        quote_stack = defaultdict(list)
        with requests.session() as sess:
            while True:
                quote = self._submit_request(sess,
                                             asset_id, start, end, resolution)
                status = quote.pop("s")
                if "ok" == status:
                    quote.pop("vo")
                    quote.pop("v")

                    for k, v in quote.items():
                        quote_stack[k].extend(v)

                elif status == "no_data":
                    break

                q_start, q_end = self._batch_query_state(quote_stack)
                logger.info("start:{}, end:{}".format(q_end, end))
                if q_end >= end - BDay():
                    break
                else:
                    start = q_end
            return self._to_dataframe(quote_stack)

    def _submit_request(self, sess, asset_id, start, end, resolution):
        req_info = self.zombie_info
        from_ = start
        to_ = end
        req_info["from_"] = from_
        req_info["to_"] = to_
        req_info["resolution"] = resolution
        req_info["pair_ID"] = asset_id
        url = self.mkt_quotes_url(req_info)
        logger.info(url)
        quote = sess.post(
            url,
            headers={"User-Agent":
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                     "X-Requested-With": "XMLHttpRequest"})
        quote = json.loads(quote.text)
        return quote

    @staticmethod
    def _batch_query_state(quote):
        start = datetime.datetime.fromtimestamp(min(quote["t"]))
        end = datetime.datetime.fromtimestamp(max(quote["t"]))
        return start, end

    def _to_dataframe(self, quote):
        if len(quote["t"]) > 0:
            d_ = pd.DataFrame(quote)
            d_.rename({"t": "date", "c": "PX_LAST", "o": "PX_OPEN",
                       "h": "PX_HIGH", "l": "PX_LOW"}, axis=1, inplace=True)

            d_["date"] = d_["date"].apply(
                lambda x: datetime.datetime.fromtimestamp(x))  # local time
            d_.set_index("date", inplace=True)
        else:
            return []
        return d_

    def get_batch(self, symbols, start, end, resolution):
        missions = {}

        for i in symbols:
            missions[(i, start, end)] = False

        async def async_crawl():
            with ThreadPoolExecutor(max_workers=10) as executor:
                with requests.Session() as sess:
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(
                            executor, self.get,
                            *(sess, k[0], k[1], k[2], resolution))
                        for k, v in missions.items()
                    ]
                    for response in await asyncio.gather(*tasks):
                        pass
            return tasks

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(async_crawl())
        loop.run_until_complete(future)
        data = {symbols[i]: v.result() for i, v in enumerate(future.result())}
        return data

    def __make_daterange(self, start, end):
        Ms = [datetime.datetime.strptime(str(start), "%Y%m%d"),
              datetime.datetime.strptime(str(end), "%Y%m%d")]
        return Ms

    def get_zombie_info(self):
        hist_url = "https://tvc4.forexpros.com"
        req = requests.get(hist_url, headers=self.default_headers)
        parser = BeautifulSoup(req.text, "lxml")
        zombie_info_text = parser.find("iframe")['src']
        return self.zombie_parser(zombie_info_text)

    @staticmethod
    def searching_api(asset_name):
        search_url = "https://www.investing.com/search/service/search"
        form_data = {"search_text": asset_name, "term": asset_name,
                     "country_id": 0, "tab_id": "All"}
        req = requests.post(
            search_url, data=form_data,
            headers={"User-Agent":
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                     "DNT": "1", "Host": "www.investing.com", "Origin": "https://www.investing.com",
                     "Referer": "https://www.investing.com/currencies/live-currency-cross-rates",
                     "X-Requested-With": "XMLHttpRequest"})
        return req.json()

    @staticmethod
    def zombie_parser(url):
        url = urllib.parse.urlparse(url)
        info_dict = urllib.parse.parse_qs(url.query)
        return info_dict

    @staticmethod
    def gen_url_from_zombie_info(template, zombie_info):
        template = template.replace(" ", "")
        return template.format(*zombie_info["carrier"], *zombie_info["time"],
                               *zombie_info["domain_ID"], *
                               zombie_info["lang_ID"],
                               *zombie_info["timezone_ID"], zombie_info["pair_ID"],
                               int(time.mktime(
                                   zombie_info["from_"].timetuple())),
                               int(time.mktime(
                                   zombie_info["to_"].timetuple())),
                               zombie_info["resolution"])

    def mkt_quotes_url(self, zombie_info):
        template = "https://tvc4.forexpros.com/{}/{}/{}/{}/{}/history?symbol={}\
        &from={}&to={}&resolution={}"
        return self.gen_url_from_zombie_info(template, zombie_info)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    def test():
        price_api = InvestingDotComAPI()
        event_api = EcoEventAPI()
        with requests.Session() as sess:
            _ = price_api.get(sess, "USDKRW", datetime.datetime(2019, 1, 15),
                              datetime.datetime(2019, 2, 1), "15")
            # _ = event_api.get(sess,
            #                  "US", start=datetime.datetime(2020, 1, 1),
            #                  end=datetime.datetime(2020, 1, 15))
    test()
