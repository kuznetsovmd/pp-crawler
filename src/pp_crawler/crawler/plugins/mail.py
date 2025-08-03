from bs4 import BeautifulSoup

from pp_crawler.crawler.plugins.base_analytics import BaseAnalytics


def template1(soup: BeautifulSoup) -> list[str]:
    return [
        p.select_one("a.t90.t_grey")["href"]
        for p in {a.parent for a in soup.select("td.it-title > a.t90.t_grey")}
    ]


class Mail(BaseAnalytics):
    def __init__(
        self,
        keywords: list[str],
        pages: int,
        descriptor: str,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__(
            "https://top.mail.ru/Rating/{keyword}/Month/Visitors/{page}.html",
            (template1,),
            keywords,
            pages,
            descriptor,
            cooldown,
            random_cooldown,
        )
