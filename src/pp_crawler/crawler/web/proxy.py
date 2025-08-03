import re
import requests

from http_request_randomizer.requests.proxy.ProxyObject import Protocol
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy


class Proxy:
    _instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = _Proxy(*args, **kwargs)
        return cls._instance


class _Proxy:
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
        return p.group(1), int(p.group(2))

    def get_proxy(self):
        from core.functions import get_logger

        logger = get_logger()

        while True:
            p = self.proxies_list.pop(0).get_address()

            try:
                logger.info(f"Trying {p}")
                proxy = {"http": f"http://{p}", "https": f"https://{p}"}

                ip = _Proxy.ip.search(
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
