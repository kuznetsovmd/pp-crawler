import re
from typing import Optional

from bs4 import Tag

from pp_crawler.core.functions import get_logger


def compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p.replace(" ", ".*"), re.IGNORECASE) for p in patterns]


class LinkMatcher:
    def __init__(self, privacy_links: list[str]):
        self.logger = get_logger()
        self.regexes = compile_patterns(privacy_links)
        self.href_re = re.compile(r"^((https?://)?(www\.)?([\w.\-_]+)\.\w+)?(.*$)")
        self.http_re = re.compile(r"https?:(//)?")

    def match(self, website: str, body: Tag) -> Optional[str]:
        try:
            for link in reversed(body.find_all("a")):
                if not isinstance(link, Tag):
                    continue

                text = link.text.lower().strip()
                if not any(r.match(text) for r in self.regexes):
                    return None

                href = link.get("href")
                if not isinstance(href, str):
                    return None

                if ref := self.href_re.match(href):
                    cleaned_url = self.http_re.sub("", website)
                    return f"http://{cleaned_url}{ref.group(5)}"

        except (AttributeError, TypeError):
            pass

        return None
