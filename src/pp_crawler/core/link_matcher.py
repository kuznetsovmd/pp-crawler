import re

from bs4 import BeautifulSoup

from pp_crawler.core.functions import get_logger


def compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p.replace(" ", ".*"), re.IGNORECASE) for p in patterns]


class LinkMatcher:
    def __init__(self, privacy_links: list[str]):
        self.logger = get_logger()
        self.regexes = compile_patterns(privacy_links)
        self.href_re = re.compile(r"^((https?://)?(www\.)?([\w.\-_]+)\.\w+)?(.*$)")
        self.http_re = re.compile(r"https?:(//)?")

    def match(self, website: str, soup: BeautifulSoup) -> str:
        try:
            for link in reversed(soup.find_all("a")):
                text = link.text.lower().strip()
                if any(r.match(text) for r in self.regexes):
                    href = link.get("href")
                    if ref := self.href_re.match(href or ""):
                        cleaned_url = self.http_re.sub("", website)
                        return f"http://{cleaned_url}{ref.group(5)}"
        except (AttributeError, TypeError):
            pass
