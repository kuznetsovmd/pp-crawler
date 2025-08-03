from functools import partial
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Callable, Optional

from bs4 import Tag

from pp_crawler.core.functions import (
    concat_files,
    gen_search_urls,
    get_logger,
    get_soup_from_url,
    load_last_id_page,
    read_models,
    skip_to,
    temp_descriptor,
    write_models,
)
from pp_crawler.crawler.plugins.plugin import Plugin
from pp_crawler.crawler.website import Website


def find_urls(
    args: tuple[str, str],
    templates: list[Callable[[Tag], list[str]]],
    cooldown: float = 0.0,
    random_cooldown: float = 0.0,
) -> tuple[str, str, set[str]]:
    page_url, keyword = args
    logger = get_logger()

    if not page_url:
        return keyword, page_url, set()

    soup = get_soup_from_url(page_url, cooldown, random_cooldown)
    if not soup:
        return keyword, page_url, set()

    urls: set[str] = set()
    for template in templates:
        urls.update(template(soup))

    if urls:
        logger.info(f"Found urls:\n\t{'\n\t'.join(urls)}")

    return keyword, page_url, urls


class BaseAnalytics(Plugin):
    def __init__(
        self,
        search_url: str,
        templates: list[Callable[[Tag], list[str]]],
        keywords: list[Optional[str]],
        pages: int,
        descriptor: Path,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__()
        self.logger = get_logger()
        self.descriptor = Path(descriptor)
        self.search_url = search_url
        self.templates = templates
        self.keywords = keywords
        self.pages = pages
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown

    def scrap_records(self, pool: Pool) -> None:
        get_logger().info(f"Searching on {self.__class__.__name__}")

        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        desc_id, _ = load_last_id_page(self.descriptor)
        last_id, last_page = load_last_id_page(tmp1)
        Website._counter = max(int(desc_id or 0), int(last_id or 0)) + 1

        worker_func = partial(
            find_urls,
            templates=self.templates,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        urls_iter = gen_search_urls(self.search_url, self.keywords, self.pages)
        skipped_iter = skip_to(urls_iter, last_page, key=lambda x: x[0])

        for keyword, page, urls in pool.imap(worker_func, skipped_iter):
            write_models(
                tmp1,
                [Website(website=u, keyword=keyword, page=page) for u in urls],
                mode="a",
            )

        for i, model in enumerate(
            read_models(tmp1, Website), start=int(desc_id or 0) + 1
        ):
            model.id = i
            write_models(tmp2, [model], mode="a")

        tmp2.replace(tmp1)
        concat_files([self.descriptor, tmp1], tmp2)
        tmp2.replace(self.descriptor)
