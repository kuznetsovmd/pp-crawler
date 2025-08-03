# mypy: disable-error-code=no-untyped-call
import os
import random
import tempfile
from pathlib import Path
from time import sleep
from typing import Any, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

from pp_crawler.core.config import DriverConfig
from pp_crawler.core.exceptions import CaptchaException


def inject_js(filename: str) -> str:
    module_dir = Path(__file__).parent
    js_path = module_dir / "javascript" / filename
    with open(js_path, "r", encoding="utf-8") as f:
        return f.read()


class _DriverInstance:
    def __init__(self, conf: DriverConfig):
        from pp_crawler.core.functions import get_logger

        self.logger = get_logger()
        self.logger.setLevel(conf.log_level)

        self._sanitize = inject_js("sanitize.js")
        self._conf = conf

        tempfile.tempdir = str(conf.temp_dir)
        os.makedirs(conf.temp_dir, exist_ok=True)
        self._driver = self.make_driver(conf)

    def make_driver(self, conf: DriverConfig) -> webdriver.Firefox:
        profile = None
        if conf.profile_path:
            self.logger.info(f"Using profile: {conf.profile_path}")
            profile = webdriver.FirefoxProfile(conf.profile_path)

        else:
            self.logger.warning("Using temporary profile")
            profile = webdriver.FirefoxProfile()

        if conf.no_cache:
            profile.set_preference("browser.cache.disk.enable", False)
            profile.set_preference("browser.cache.memory.enable", False)
            profile.set_preference("browser.cache.offline.enable", False)
            profile.set_preference("network.http.use-cache", False)
            profile.set_preference("dom.webdriver.enabled", False)
            profile.set_preference("marionette.enabled", False)

        if conf.private:
            profile.set_preference("browser.privatebrowsing.autostart", True)

        profile.set_preference(
            "general.useragent.override", random.choice(conf.user_agents)
        )
        profile.set_preference("intl.accept_languages", "en-US, en")
        profile.update_preferences()

        options = Options()
        options.add_argument("--no-sandbox")
        if conf.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.profile = profile

        executable_path = None
        try:
            with open(conf.dotfile, "r") as f:
                executable_path = f.read().strip()
        except FileNotFoundError:
            self.logger.error(f"Dotfile with executable path not found: {conf.dotfile}")
            raise

        service = Service(
            executable_path=executable_path, log_output=str(conf.log_path)
        )

        driver = webdriver.Firefox(options=options, service=service)
        driver.set_page_load_timeout(conf.page_load_timeout)
        driver.set_script_timeout(conf.page_load_timeout)
        driver.execute_script(inject_js("sanitize.js"))
        return driver

    def get(
        self,
        url: str,
        cooldown: float = 0.0,
        random_cooldown: float = 0.0,
        remove_invisible: bool = False,
    ) -> None:
        if not url:
            raise ValueError("Null url")

        self.logger.info(f"Going to {url}")

        network_error, timeout_error, captcha_error = 0, 0, 0
        while (
            network_error < self._conf.max_error_attempts
            and captcha_error < self._conf.max_captcha_attempts
            and timeout_error < self._conf.max_timeout_attempts
        ):
            try:
                self.sleep(cooldown, random_cooldown)
                self._driver.get(url)

                try:
                    alert = self._driver.switch_to.alert
                    alert.accept()
                    self.logger.info("Alert accepted")
                except NoAlertPresentException:
                    pass

                try:
                    self._driver.find_element(
                        By.XPATH, "//iframe[contains(@src, 'recaptcha')]"
                    )
                    captcha_error += 1
                    raise CaptchaException
                except NoSuchElementException:
                    pass

                if remove_invisible:
                    self.remove_invisible()

                return

            except TimeoutException:
                self.logger.warning(f"Slow connection, retying {url}")
                self._driver.quit()
                self._driver = self.make_driver(self._conf)
                timeout_error += 1

            except WebDriverException:
                self.logger.warning(
                    f"Web driver exception, potentially net error, retying {url}"
                )
                self._driver.quit()
                self._driver = self.make_driver(self._conf)
                network_error += 1

            except CaptchaException:
                self.logger.warning(f"Captcha detected, retying {url}")
                self._driver.quit()
                self._driver = self.make_driver(self._conf)
                captcha_error += 1

    @classmethod
    def sleep(cls, cooldown: float = 0.0, random_cooldown: float = 0.0) -> None:
        sleep(cooldown + random.random() * random_cooldown)

    def source(self) -> str:
        return self._driver.page_source

    def wait(self, event: Any, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self._driver, timeout).until(event)
            return True
        except TimeoutException:
            self.logger.warning("Wait timeout")
        return False

    def find_element(self, by: str, value: str | None) -> WebElement:
        return self._driver.find_element(by, value)

    def remove_invisible(self) -> None:
        self._driver.execute_script(self._sanitize)

    def quit(self) -> None:
        self._driver.quit()
        self.logger.info("Driver has been closed")


class Driver:
    _instance: Optional[_DriverInstance] = None
    _config: Optional[DriverConfig] = None

    @classmethod
    def spawn(cls, *args: Any, **kwargs: Any) -> _DriverInstance:
        if cls._instance:
            return cls._instance
        if cls._config:
            cls._instance = _DriverInstance(cls._config)
            return cls._instance
        raise ValueError("Config is not set!")

    @classmethod
    def set_config(cls, config: DriverConfig) -> None:
        cls._config = config

    @classmethod
    def close(cls) -> None:
        if cls._instance:
            cls._instance.quit()
            cls._instance = None

    @classmethod
    def check_installation(cls, conf: DriverConfig) -> None:
        from pp_crawler.core.functions import get_logger

        logger = get_logger()
        logger.info("Checking installed driver")

        try:
            with open(conf.dotfile, "r") as f:
                executable_path = f.read()
                if executable_path:
                    logger.info(f"Driver found at {executable_path}")
                    return
                raise FileNotFoundError

        except FileNotFoundError:
            logger.info("Driver is not found, installing...")
            executable_path = GeckoDriverManager().install()
            with open(conf.dotfile, "w") as f:
                f.write(executable_path)
