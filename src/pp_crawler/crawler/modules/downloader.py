from functools import partial
from hashlib import md5
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Tag

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
from pp_crawler.crawler.modules.module import Module
from pp_crawler.crawler.web.driver import Driver


def download_and_hash(policy: str, html_dir: Path) -> tuple[str, Optional[str]]:
    driver = Driver.spawn()
    driver.get(policy, remove_invisible=True)

    markup = driver.source()
    if not markup:
        return policy, None

    body = BeautifulSoup(markup, "lxml").find("body")
    if not isinstance(body, Tag):
        return policy, None

    pretty_body = body.prettify()

    if isinstance(pretty_body, bytes):
        pretty_body = pretty_body.decode("utf-8")

    content = (
        "<html>\n"
        "<head>\n"
        '\t<meta charset="utf-8"/>\n'
        "\t<title></title>\n"
        "</head>\n"
        f"{pretty_body.replace('\t', ' ' * 4)}\n"
        "</html>"
    )
    content_hash = md5(content.encode()).hexdigest()

    with open(html_dir / f"{content_hash}.html", "w", encoding="utf-8") as f:
        f.write(content)

    get_logger().info(f"Downloaded policy: {policy}")
    return policy, content_hash


class Downloader(Module):
    def __init__(self, cls, descriptor, explicit, html, chunk_size=64):
        self.cls = cls
        self.descriptor = descriptor
        self.explicit = explicit
        self.html = html
        self.chunk_size = chunk_size

    def run(self, pool: Pool) -> None:
        get_logger().info("Downloading policies")

        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "combined")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp3 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        worker_func = partial(download_and_hash, html_dir=self.html)

        concat_files([self.descriptor, self.explicit], tmp1)
        last_id, _ = load_last_id_page(tmp2)

        models_iter = read_models(tmp1, self.cls)
        skipped_iter = skip_to(models_iter, last_id, lambda x: x.id)

        p_cache = dict()
        for models in chunked(skipped_iter, self.chunk_size):
            new_policies = [m.policy for m in models if m.policy and m.policy not in p_cache]

            for policy, content_hash in pool.imap(worker_func, new_policies):
                p_cache[policy] = content_hash

            for m in models:
                m.hash = p_cache.get(m.policy, None)

            write_models(tmp2, models, mode="a")

        concat_files([tmp2], tmp3)
        tmp3.replace(self.descriptor)
