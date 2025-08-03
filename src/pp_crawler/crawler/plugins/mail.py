from pathlib import Path

from bs4 import Tag

from pp_crawler.crawler.plugins.base_analytics import BaseAnalytics


def template1(body: Tag) -> list[str]:
    result = []
    parents = {a.parent for a in body.select("td.it-title > a.t90.t_grey")}
    for p in parents:
        if not isinstance(p, Tag):
            return []

        a_tag = p.select_one("a.t90.t_grey")
        if not a_tag or "href" not in a_tag.attrs:
            return []

        href = a_tag["href"]
        if isinstance(href, str):
            result.append(href)

    return result


class Mail(BaseAnalytics):
    def __init__(
        self,
        keywords: list[str | None],
        pages: int,
        descriptor: Path,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__(
            "https://top.mail.ru/Rating/{keyword}/Month/Visitors/{page}.html",
            [template1],
            keywords,
            pages,
            descriptor,
            cooldown,
            random_cooldown,
        )
