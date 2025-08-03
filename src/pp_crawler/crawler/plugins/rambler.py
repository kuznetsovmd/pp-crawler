from bs4 import BeautifulSoup

from pp_crawler.crawler.plugins.base_analytics import BaseAnalytics


def template1(soup: BeautifulSoup) -> list[str]:
    return [
        a.get("href")
        for a in soup.select("tr > td > div > div > div > a")
        if a.get("href")
    ]


class Rambler(BaseAnalytics):
    def __init__(
        self,
        pages: int,
        descriptor: str,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__(
            "https://top100.rambler.ru/navi/?period=month&sort=viewers&page={page}&_openstat=catalogue_top100",
            (template1,),
            [None],
            pages,
            descriptor,
            cooldown,
            random_cooldown,
        )
