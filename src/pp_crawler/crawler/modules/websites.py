from pathlib import Path
from functools import partial
from multiprocessing.pool import Pool
from typing import TypeVar

from pp_crawler.crawler.engines.engine import Engine
from pp_crawler.crawler.modules.module import Module
from pp_crawler.crawler.product import Product
from pp_crawler.core.functions import (
    chunked,
    concat_files,
    get_logger,
    load_last_id_page,
    read_models,
    skip_to,
    temp_descriptor,
    write_models,
)


T = TypeVar("T", bound=Engine)


def search_website(
    data: tuple[str, str],
    engines: list[T],
    cooldown: float = 2.0,
    random_cooldown: float = 2.0,
) -> tuple[str, str]:
    manufacturer, keyword = data

    logger = get_logger()

    for engine in engines:
        if site := engine.search(manufacturer, keyword, cooldown, random_cooldown):
            logger.info(f"Found website: {site}")
            return manufacturer, site

    return manufacturer, None


class Websites(Module):
    def __init__(
        self,
        descriptor: Path,
        engines: list[T],
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
        chunk_size: int = 64,
    ):
        self.descriptor = descriptor
        self.engines = engines
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.chunk_size = chunk_size

    def run(self, pool: Pool = None) -> None:
        get_logger().info("Searching websites")

        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        search_func = partial(
            search_website,
            engines=self.engines,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        last_id, _ = load_last_id_page(tmp1)

        products_iter = read_models(self.descriptor, Product)
        skipped_iter = skip_to(products_iter, last_id, lambda x: x.id)

        ws_cache = dict()
        for models in chunked(skipped_iter, self.chunk_size):
            models = list(models)
            pairs = [
                (m.manufacturer, m.keyword.replace("+", " ") if m.keyword else "")
                for m in models
                if m.manufacturer and m.manufacturer not in ws_cache
            ]

            for manufacturer, website in pool.imap(search_func, pairs):
                ws_cache[manufacturer] = website

            for m in models:
                m.website = ws_cache.get(m.manufacturer, None)

            write_models(tmp1, models, mode="a")

        concat_files([tmp1], tmp2)
        tmp2.replace(self.descriptor)
