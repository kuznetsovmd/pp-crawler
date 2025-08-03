import argparse
import atexit
import json
import sys
import logging
import signal
import logging.handlers
from pprint import pprint
from multiprocessing import Queue
from multiprocessing import Process
from multiprocessing import Pool

from pp_crawler.crawler.web.driver import Driver
from pp_crawler.core.functions import get_logger, init_files, load_constructor
from pp_crawler.core.config import Config, DriverConfig


class ExitFilter(logging.Filter):
    def filter(self, record):
        if not record.exc_info:
            return True
        _, exc_value, _ = record.exc_info
        return not isinstance(exc_value, (SystemExit, BrokenPipeError))


def sysexit(*_):
    logger = get_logger()
    logger.info("Closing worker")
    raise SystemExit(0)


def init_logger(queue):
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    h = logging.handlers.QueueHandler(queue)
    root.addHandler(h)


def worker_constructor(queue, config: DriverConfig):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, sysexit)
    atexit.register(worker_destructor)
    init_logger(queue)
    Driver.set_config(config)


def worker_destructor():
    Driver.close()


def logger_initializer(queue):
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


def main():
    sys.stderr = open(".stderr.log", "a", buffering=1)

    parser = argparse.ArgumentParser(
        prog="privacy-sanitization",
        description="Command line tool to control sanitization framework",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to JSON file with configuration (default is config.json)",
    )
    args = parser.parse_args()
    pprint(args)

    with open(args.config) as f:
        cfg = json.load(f)

    c = Config.build(**cfg)
    pprint(c)
    init_files(c.path)

    queue = Queue(-1)
    logger_process = Process(target=logger_initializer, args=(queue,))
    logger_process.start()

    init_logger(queue)

    logger = get_logger()
    logger.info(f"Using thread count: {c.proc_count}")

    Driver.check_installation(c.driver)

    p = Pool(c.proc_count, initializer=worker_constructor, initargs=(queue, c.driver))

    try:
        pipeline = load_constructor(c.pipeline)
        for m in pipeline(c):
            m.run(p)
        p.close()

    except KeyboardInterrupt:
        logger.info("Keyboard interruption, closing gracefully")
        p.terminate()
        raise

    except Exception:
        p.terminate()
        raise

    finally:
        p.join()

        logger.info("Shutting down")
        queue.put_nowait(None)
        logger_process.join()

    return 0


if __name__ == "__main__":
    default_stderr = sys.stderr
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        sys.stderr = default_stderr
        raise
