from typing import TypeVar
from pp_crawler.core.config import Config
from pp_crawler.core.link_matcher import LinkMatcher
from pp_crawler.crawler.engines.google import GoogleEngine
from pp_crawler.crawler.modules.downloader import Downloader
from pp_crawler.crawler.modules.module import Module
from pp_crawler.crawler.modules.policies import Policies
from pp_crawler.crawler.modules.urls import Urls
from pp_crawler.crawler.modules.websites import Websites
from pp_crawler.crawler.plugins.amazon import Amazon
from pp_crawler.crawler.plugins.walmart import Walmart
from pp_crawler.crawler.product import Product


T = TypeVar("T", bound=Module)


def pipeline(c: Config) -> list[T]:
    return [
        Urls(
            [
                Amazon(
                    [
                        "voice controller",
                        "outdoor camera",
                        "indoor camera",
                        "tracking device",
                        "tracking sensor",
                        "gps tracking device",
                        "smart air purifier",
                        "robot vacuum cleaner",
                        "smart video doorbell",
                        "smart air conditioner",
                        "smart thermometer",
                        "smart speaker",
                        "smart tv",
                        "smart light switch",
                        "smart plug",
                        "smart thermostat",
                        "smart alarm clock",
                        "smart navigation system",
                        "smart bulb",
                        "smart lock",
                        "smart bracelet",
                        "smart watch",
                        "smart scale",
                    ],
                    1,
                    c.path.descriptor_file,
                    cooldown=1.0,
                    random_cooldown=5.0,
                ),
                Walmart(
                    [
                        "voice controller",
                        "outdoor camera",
                        "indoor camera",
                        "tracking device",
                        "tracking sensor",
                        "gps tracking device",
                        "smart air purifier",
                        "robot vacuum cleaner",
                        "smart video doorbell",
                        "smart air conditioner",
                        "smart thermometer",
                        "smart speaker",
                        "smart tv",
                        "smart light switch",
                        "smart plug",
                        "smart thermostat",
                        "smart alarm clock",
                        "smart navigation system",
                        "smart bulb",
                        "smart lock",
                        "smart bracelet",
                        "smart watch",
                        "smart scale",
                    ],
                    1,
                    c.path.descriptor_file,
                    cooldown=1.0,
                    random_cooldown=5.0,
                ),
            ]
        ),
        Websites(
            c.path.descriptor_file,
            [GoogleEngine(similarity_threshold=0.7, cooldown=2.0, random_cooldown=2.0)],
        ),
        Policies(
            Product,
            c.path.descriptor_file,
            LinkMatcher((r"privacy policy",)),
        ),
        Downloader(
            Product,
            c.path.descriptor_file,
            c.path.explicit_file,
            c.path.html_path,
        ),
    ]
