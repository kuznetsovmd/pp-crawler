import atexit
import logging
import logging.handlers
import signal
import sys
from multiprocessing.queues import Queue
from typing import Any

from pp_crawler.core.config import DriverConfig
from pp_crawler.core.functions import get_logger
from pp_crawler.crawler.web.driver import Driver


class ExitFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not record.exc_info:
            return True
        _, exc_value, _ = record.exc_info
        return not isinstance(exc_value, (SystemExit, BrokenPipeError))


def sysexit(*_: Any) -> None:
    logger = get_logger()
    logger.info("Closing worker")
    raise SystemExit(0)


def init_logger(queue: Queue[Any]) -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    h = logging.handlers.QueueHandler(queue)
    root.addHandler(h)


def worker_constructor(queue: Queue[Any], config: "DriverConfig") -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, sysexit)
    atexit.register(worker_destructor)
    init_logger(queue)
    Driver.set_config(config)


def worker_destructor() -> None:
    Driver.close()


def logger_initializer(queue: Queue[Any]) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    f = logging.Formatter(
        "%(asctime)s - [%(name)s] %(levelname)s: %(message)s", "%H:%M:%S"
    )
    h = logging.StreamHandler(sys.stdout)
    h.addFilter(ExitFilter())
    h.setLevel(logging.INFO)
    h.setFormatter(f)
    logging.getLogger().addHandler(h)
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)
