from pathlib import Path

from bs4 import Tag

from pp_crawler.crawler.plugins.base_analytics import BaseAnalytics


def template1(body: Tag) -> list[str]:
    hrefs = []
    for a in body.select("tr > td > div > div > div > a"):
        if not isinstance(a, Tag):
            continue

        href = a.get("href")
        if isinstance(href, str):
            hrefs.append(href)

    return hrefs


class Rambler(BaseAnalytics):
    def __init__(
        self,
        pages: int,
        descriptor: Path,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__(
            "https://top100.rambler.ru/navi/?period=month&sort=viewers&page={page}&_openstat=catalogue_top100",
            [template1],
            [None],
            pages,
            descriptor,
            cooldown,
            random_cooldown,
        )
