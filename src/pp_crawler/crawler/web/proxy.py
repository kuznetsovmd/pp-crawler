import re
from typing import Optional

import requests
from http_request_randomizer.requests.proxy.ProxyObject import Protocol  # type: ignore
from http_request_randomizer.requests.proxy.requestProxy import (
    RequestProxy,
)  # type: ignore


class _ProxyInstance:
    regex = re.compile("^(.*):(.*)$")
    ip = re.compile(r"\d+\.\d+\.\d+\.\d+")

    def __init__(self, proxies: list[str], from_config: bool = True):
        self.req_proxy = RequestProxy(protocol=Protocol.HTTP)
        if from_config:
            self.proxies_list = proxies
        else:
            self.proxies_list = self.req_proxy.get_proxy_list()

    @classmethod
    def get_ip(cls):
        return cls.ip.search(requests.get("http://icanhazip.com/").text).group(0)

    @classmethod
    def parse_proxy(cls, proxy: str):
        p = cls.regex.match(proxy)
        if p is None:
            raise ValueError(f"Invalid proxy format: {proxy}")
        return p.group(1), int(p.group(2))

    def get_proxy(self):
        from pp_crawler.core.functions import get_logger

        logger = get_logger()

        while True:
            p = self.proxies_list.pop(0).get_address()

            try:
                logger.info(f"Trying {p}")
                proxy = {"http": f"http://{p}", "https": f"https://{p}"}

                ip = _ProxyInstance.ip.search(
                    requests.get("http://icanhazip.com/", proxies=proxy, timeout=2).text
                )
                if ip.group(0) is None:
                    raise Exception
                if ip.group(0) == self.get_ip():
                    raise Exception
                if (
                    requests.get(
                        "http://google.com/", proxies=proxy, timeout=5
                    ).status_code
                    != 200
                ):
                    raise Exception

                return self.parse_proxy(p)

            except IndexError:
                logger.info("Loading more proxies")
                self.proxies_list = self.req_proxy.get_proxy_list()


class Proxy:
    _instance: Optional[_ProxyInstance]

    @classmethod
    def spawn(cls, *args, **kwargs) -> _ProxyInstance:
        if cls._instance:
            return cls._instance
        cls._instance = _ProxyInstance(*args, **kwargs)
        return cls._instance
