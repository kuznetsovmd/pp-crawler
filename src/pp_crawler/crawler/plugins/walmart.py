import re
from pathlib import Path
from typing import Optional

from bs4 import Tag

from pp_crawler.crawler.plugins.base_market import BaseMarket


def product_template(body: Tag) -> list[str]:
    links = []
    for item in body.find_all("a", {"class": "product-title-link"}):
        if not isinstance(item, Tag):
            continue

        href = item.get("href")
        if isinstance(href, str):
            links.append(f"https://www.walmart.com{href}")

    return links


def template1(body: Tag) -> Optional[str]:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]", flags=re.IGNORECASE)

    table = body.find("table", {"class": "product-specification-table"})
    if not isinstance(table, Tag):
        return None

    tbody = table.find("tbody")
    if not isinstance(tbody, Tag):
        return None

    for tr in tbody.find_all("tr"):
        if not isinstance(tr, Tag):
            continue

        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        label = sanitize_label.sub("", tds[0].text)
        if is_manufacturer.fullmatch(label):
            manufacturer = tds[1].text
            return sanitize_value.sub("", manufacturer).lower().strip()

    return None


def template2(body: Tag) -> Optional[str]:
    is_brand = re.compile(r"^brand$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]", flags=re.IGNORECASE)

    table = body.find("table", {"class": "product-specification-table"})
    if not isinstance(table, Tag):
        return None

    tbody = table.find("tbody")
    if not isinstance(tbody, Tag):
        return None

    for tr in tbody.find_all("tr"):
        if not isinstance(tr, Tag):
            continue

        tds = tr.find_all("td")
        if not isinstance(tds, Tag):
            continue

        if len(tds) < 2:
            continue

        label = sanitize_label.sub("", tds[0].text)
        if is_brand.fullmatch(label):
            manufacturer = tds[1].text
            return sanitize_value.sub("", manufacturer).lower().strip()

    return None


class Walmart(BaseMarket):
    def __init__(
        self,
        keywords: list[str],
        pages: int,
        descriptor: Path,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__(
            "https://www.walmart.com/search/?page={page}&ps=40&query={keyword}",
            product_template,
            [template1, template2],
            [k.replace(" ", "+") for k in keywords],
            pages,
            descriptor,
            30,
            cooldown,
            random_cooldown,
        )
