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
from pp_crawler.crawler.product import Product


def find_product_links(
    data: tuple[str, str],
    template: Callable[[Tag], list[str]],
    cooldown: float = 0.0,
    random_cooldown: float = 0.0,
) -> tuple[str, str, set[str]]:
    url, keyword = data
    logger = get_logger()

    if not url:
        return keyword, url, set()

    soup = get_soup_from_url(url, cooldown, random_cooldown)
    if not soup:
        return keyword, url, set()

    products = set(template(soup))
    if products:
        logger.info(f"Found products:\n\t{'\n\t'.join(products)}")

    return keyword, url, products


def find_manufacturer(
    product: Product,
    templates: list[Callable[[Tag], Optional[str]]],
    cooldown: float = 0.0,
    random_cooldown: float = 0.0,
) -> Product:
    logger = get_logger()

    if not product.url:
        return product

    soup = get_soup_from_url(product.url, cooldown, random_cooldown)
    if not soup:
        return product

    for template in templates:
        if manufacturer := template(soup):
            product.manufacturer = manufacturer
            logger.info(f"Found manufacturer: {manufacturer}")
            return product

    return product


class BaseMarket(Plugin):
    def __init__(
        self,
        search_url: str,
        product_template: Callable[[Tag], list[str]],
        templates: list[Callable[[Tag], Optional[str]]],
        keywords: list[Optional[str]],
        pages: int,
        descriptor: Path,
        chunk_size: int = 64,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        self.logger = get_logger()
        self.search_url = search_url
        self.descriptor = Path(descriptor)
        self.keywords = keywords
        self.pages = pages
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.product_template = product_template
        self.templates = templates
        self.chunk_size = chunk_size

    def scrap_records(self, pool: Pool) -> None:
        get_logger().info(f"Searching on {self.__class__.__name__}")

        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        desc_id, _ = load_last_id_page(self.descriptor)
        last_id, last_page = load_last_id_page(tmp1)
        Product._counter = max(int(desc_id or 0), int(last_id or 0)) + 1

        product_func = partial(
            find_product_links,
            template=self.product_template,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        urls_iter = gen_search_urls(self.search_url, self.keywords, self.pages)
        skipped_iter = skip_to(urls_iter, last_page)
        for keyword, page, urls in pool.imap(product_func, skipped_iter):
            write_models(
                tmp1,
                [Product(url=u, keyword=keyword, page=page) for u in urls],
                mode="a",
            )

        manufacturer_func = partial(
            find_manufacturer,
            templates=self.templates,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        last_id, _ = load_last_id_page(tmp2)

        models_iter = read_models(self.descriptor, Product)
        skipped_iter = skip_to(models_iter, last_id)

        for product in pool.imap(manufacturer_func, skipped_iter):
            write_models(tmp2, [product], mode="a")

        for i, model in enumerate(read_models(tmp1, Product), start=int(desc_id or 0) + 1):
            model.id = i
            write_models(tmp2, [model], mode="a")

        tmp2.replace(tmp1)
        concat_files([self.descriptor, tmp1], tmp2)
        tmp2.replace(self.descriptor)
