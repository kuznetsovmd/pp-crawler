import re
from difflib import SequenceMatcher

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from pp_crawler.crawler.engines.engine import Engine
from pp_crawler.crawler.web.driver import Driver


class GoogleEngine(Engine):
    def __init__(self, similarity_threshold=0.6, cooldown=0.0, random_cooldown=0.0):
        super().__init__()
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.similarity = similarity_threshold
        self.regex_href = re.compile(r"^((https?://)?(www\.)?([\w.\-_]+)(\.\w+)).*$")
        self.regex_request = re.compile(r"[^\w ]+|\s{2,}")

    def search(self, manufacturer, keyword):
        driver = Driver()
        driver.get("https://www.google.com")

        search = driver.find_element(By.NAME, "q")
        search.send_keys(f"{manufacturer} {keyword}", Keys.RETURN)

        driver.wait(ec.presence_of_element_located((By.TAG_NAME, "cite")))

        markup = driver.source()
        if not markup:
            return None

        soup = BeautifulSoup(markup, "lxml").body
        if not soup:
            return None

        return self.similarity_filter(manufacturer, soup, threshold=self.similarity)

    def similarity_filter(self, content, soup, threshold=0.6):
        best_url = None
        best_similarity = threshold

        content_list = self.regex_request.sub(" ", content).split()
        if len(content_list) > 1:
            content_list.append("".join(content_list))

        for cite in soup.find_all("cite"):
            m = self.regex_href.match(cite.text)
            if not m:
                break

            domain = m.group(4)
            for piece in content_list:
                sim = SequenceMatcher(None, piece, domain).ratio()
                if sim > best_similarity or domain in piece:
                    w3 = m.group(3) or ""
                    best_url = f"http://{w3}{domain}{m.group(5)}"
                    best_similarity = sim

        return best_url
