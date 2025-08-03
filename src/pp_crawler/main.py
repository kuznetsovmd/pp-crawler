import argparse
import json
import sys
from multiprocessing import Pool, Process, Queue
from pprint import pprint
from typing import Any

from pp_crawler.core.config import Config
from pp_crawler.core.functions import get_logger, init_files, load_constructor
from pp_crawler.core.pool import init_logger, logger_initializer, worker_constructor
from pp_crawler.crawler.web.driver import Driver


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pp_crawler",
        description="Command line tool to control web crawling framework",
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

    queue: Queue[Any] = Queue(-1)
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
        return 0

    except KeyboardInterrupt:
        logger.info("Keyboard interruption, closing gracefully")
        p.terminate()
        return 130

    except Exception:
        p.terminate()
        raise

    finally:
        p.join()

        logger.info("Shutting down")
        queue.put_nowait(None)
        logger_process.join()


if __name__ == "__main__":
    default_stderr = sys.stderr
    try:
        sys.exit(main())
    except:
        sys.stderr = default_stderr
        raise
