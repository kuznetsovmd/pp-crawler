import re
from pathlib import Path
from typing import Optional

from bs4 import Tag

from pp_crawler.crawler.plugins.base_market import BaseMarket


def product_template(body: Tag) -> list[str]:
    urls = []
    for items in body.find_all("div", {"data-component-type": "s-search-result"}):
        if not isinstance(items, Tag):
            continue

        a_tag = items.find("a")
        if not isinstance(a_tag, Tag):
            continue

        href = a_tag.get("href")
        if href is None:
            continue

        urls.append(f"https://www.amazon.com{href}")
    return urls


def template1(body: Tag) -> Optional[str]:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    div = body.find("div", {"id": "detailBullets_feature_div"})
    if not isinstance(div, Tag):
        return None

    ul = div.find("ul")
    if not isinstance(ul, Tag):
        return None

    for li in ul.find_all("li"):
        if not isinstance(li, Tag):
            return None

        span = li.find("span")
        if not isinstance(span, Tag):
            return None

        children = span.find_all("span")
        if not children or len(children) < 2:
            continue

        label = sanitize_label.sub("", children[0].text or "")
        if is_manufacturer.match(label):
            manufacturer = children[1].text
            manufacturer = sanitize_value.sub("", manufacturer).lower().strip()
            return manufacturer

    return None


def template2(body: Tag) -> Optional[str]:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    table = body.find("table", {"id": "productDetails_detailBullets_sections1"})
    if not isinstance(table, Tag):
        return None

    tbody = table.find("tbody")
    if not isinstance(tbody, Tag):
        return None

    for tr in tbody.find_all("tr"):
        if not isinstance(tr, Tag):
            continue

        th = tr.find("th")
        if not isinstance(th, Tag):
            continue

        span = sanitize_label.sub("", th.text or "")
        if is_manufacturer.match(span):
            td = tr.find("td")
            if not isinstance(td, Tag):
                continue
            manufacturer = sanitize_value.sub("", td.text).lower().strip()
            return manufacturer

    return None


def template3(body: Tag) -> Optional[str]:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    table = body.find("table", {"id": "productDetails_techSpec_section_1"})
    if not isinstance(table, Tag):
        return None

    tbody = table.find("tbody")
    if not isinstance(tbody, Tag):
        return None

    for tr in tbody.find_all("tr"):
        if not isinstance(tr, Tag):
            continue

        th = tr.find("th")
        if not isinstance(th, Tag):
            continue

        span = sanitize_label.sub("", th.text or "")
        if is_manufacturer.match(span):
            td = tr.find("td")
            if not isinstance(td, Tag):
                continue
            return sanitize_value.sub("", td.text).lower().strip()

    return None


class Amazon(BaseMarket):
    def __init__(
        self,
        keywords: list[str],
        pages: int,
        descriptor: Path,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
    ):
        super().__init__(
            "https://www.amazon.com/s?k={keyword}&page={page}",
            product_template,
            [template1, template2, template3],
            [k.replace(" ", "+") for k in keywords],
            pages,
            descriptor,
            30,
            cooldown,
            random_cooldown,
        )
