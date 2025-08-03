import re

from bs4 import BeautifulSoup

from pp_crawler.crawler.plugins.base_market import BaseMarket


def product_template(soup: BeautifulSoup) -> list[str]:
    return [
        f"https://www.walmart.com{item.get('href')}"
        for item in soup.findAll("a", {"class": "product-title-link"})
    ]


def template1(soup: BeautifulSoup) -> str:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    try:
        div = soup.find("table", {"class": "product-specification-table"})
        for tr in div.tbody.findChildren("tr"):
            tds = tr.findChildren("td")
            label = sanitize_label.sub("", tds[0].text)
            if is_manufacturer.search(label):
                manufacturer = tds[1].text
                return sanitize_value.sub("", manufacturer).lower().trim()

    except (AttributeError, TypeError):
        pass


def template2(soup: BeautifulSoup) -> str:
    is_brand = re.compile(r"^brand$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    try:
        div = soup.find("table", {"class": "product-specification-table"})
        for tr in div.tbody.findChildren("tr"):
            tds = tr.findChildren("td")
            label = sanitize_label.sub("", tds[0].text)
            if is_brand.search(label):
                manufacturer = tds[1].text
                return sanitize_value.sub("", manufacturer).lower().trim()

    except (AttributeError, TypeError):
        pass


class Walmart(BaseMarket):
    def __init__(
        self,
        keywords: list[str],
        pages: int,
        descriptor: str,
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
            cooldown,
            random_cooldown,
        )
