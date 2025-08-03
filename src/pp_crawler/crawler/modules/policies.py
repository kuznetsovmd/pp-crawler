from functools import partial
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Optional, TypeVar

from pp_crawler.core.functions import (
    chunked,
    concat_files,
    get_logger,
    get_soup_from_url,
    load_last_id_page,
    read_models,
    skip_to,
    temp_descriptor,
    write_models,
)
from pp_crawler.core.link_matcher import LinkMatcher
from pp_crawler.crawler.item import Item
from pp_crawler.crawler.modules.module import Module

T = TypeVar("T", bound=Item)


def find_policy(
    url: str,
    link_matcher: LinkMatcher,
    cooldown: float = 0.0,
    random_cooldown: float = 0.0,
) -> tuple[str, Optional[str]]:
    soup = get_soup_from_url(url, cooldown, random_cooldown)
    if not soup:
        return url, None

    if policy := link_matcher.match(url, soup):
        get_logger().info(f"Found policy: {policy}")
        return url, policy

    return url, None


class Policies(Module):
    def __init__(
        self,
        cls: type[T],
        descriptor: Path,
        link_matcher: LinkMatcher,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
        chunk_size: int = 64,
    ):
        self.cls = cls
        self.descriptor = descriptor
        self.link_matcher = link_matcher
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.chunk_size = chunk_size

    def run(self, pool: Pool) -> None:
        get_logger().info("Searching policies")

        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        search_func = partial(
            find_policy,
            link_matcher=self.link_matcher,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        last_id, _ = load_last_id_page(tmp1)

        models_iter = read_models(self.descriptor, self.cls)
        skipped_iter = skip_to(models_iter, last_id, lambda x: x.id)

        ws_cache = dict()
        for models in chunked(skipped_iter, self.chunk_size):
            new_websites = [m.website for m in models if m.website and m.website not in ws_cache]

            for website, policy in pool.imap(search_func, new_websites):
                ws_cache[website] = policy

            for m in models:
                m.policy = ws_cache.get(m.website, None)

            write_models(tmp1, models, mode="a")

        concat_files([tmp1], tmp2)
        tmp2.replace(self.descriptor)
