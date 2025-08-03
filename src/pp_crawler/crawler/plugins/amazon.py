import re

from bs4 import BeautifulSoup

from pp_crawler.crawler.plugins.base_market import BaseMarket


def product_template(soup: BeautifulSoup) -> list[str]:
    return [
        f"https://www.amazon.com{items.findChild('a').get('href')}"
        for items in soup.findAll("div", {"data-component-type": "s-search-result"})
    ]


def template1(soup: BeautifulSoup) -> str:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    try:
        div = soup.find("div", {"id": "detailBullets_feature_div"})
        for li in div.ul.findChildren("li"):
            span = li.span.findChildren("span")
            label = sanitize_label.sub("", span[0].text)
            if is_manufacturer.match(label):
                manufacturer = span[1].text
                manufacturer = sanitize_value.sub("", manufacturer).lower().strip()
                return manufacturer

    except (AttributeError, TypeError):
        pass


def template2(soup: BeautifulSoup) -> str:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    try:
        div = soup.find("table", {"id": "productDetails_detailBullets_sections1"})
        for tr in div.tbody.findChildren("tr"):
            span = sanitize_label.sub("", tr.th.text)
            if is_manufacturer.match(span):
                manufacturer = sanitize_value.sub("", tr.td.text).lower().strip()
                return manufacturer

    except (AttributeError, TypeError):
        pass


def template3(soup: BeautifulSoup) -> str:
    is_manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    sanitize_label = re.compile(r"[^\w]|_", flags=re.IGNORECASE)
    sanitize_value = re.compile(r"[^\w ]|_", flags=re.IGNORECASE)

    try:
        div = soup.find("table", {"id": "productDetails_techSpec_section_1"})
        for tr in div.tbody.findChildren("tr"):
            span = sanitize_label.sub("", tr.th.text)
            if is_manufacturer.match(span):
                manufacturer = sanitize_value.sub("", tr.td.text).lower().strip()
                return manufacturer

    except (AttributeError, TypeError):
        pass


class Amazon(BaseMarket):
    def __init__(
        self,
        keywords: list[str],
        pages: int,
        descriptor: str,
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
            cooldown,
            random_cooldown,
        )
