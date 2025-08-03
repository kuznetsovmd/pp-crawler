from typing import TypeVar
from pp_crawler.core.config import Config
from pp_crawler.core.link_matcher import LinkMatcher
from pp_crawler.crawler.modules.downloader import Downloader
from pp_crawler.crawler.modules.module import Module
from pp_crawler.crawler.modules.policies import Policies
from pp_crawler.crawler.modules.urls import Urls
from pp_crawler.crawler.plugins.mail import Mail
from pp_crawler.crawler.plugins.rambler import Rambler
from pp_crawler.crawler.website import Website


T = TypeVar("T", bound=Module)


def pipeline(c: Config) -> list[T]:
    return [
        Urls(
            [
                Rambler(2, c.path.descriptor_file, cooldown=1.0, random_cooldown=4.0),
                Mail(
                    ["Cars"],
                    1,
                    c.path.descriptor_file,
                    cooldown=1.0,
                    random_cooldown=4.0,
                ),
            ]
        ),
        Policies(
            Website,
            c.path.descriptor_file,
            LinkMatcher(
                (
                    r"политика конфиденциальности",
                    r"пользовательское соглашение",
                    r"политика безопасности",
                    r"правовая информация",
                    r"конфиденциальность",
                    r"условия обработки персональных данных",
                    r"правовая информация",
                )
            ),
        ),
        Downloader(
            Website,
            c.path.descriptor_file,
            c.path.explicit_file,
            c.path.html_path,
        ),
    ]
