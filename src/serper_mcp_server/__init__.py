import asyncio
import logging
import os
import sys

from dotenv import load_dotenv


def _configure_logging() -> None:
    load_dotenv()
    level_name = os.getenv("SERPER_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = os.getenv("SERPER_LOG_FILE", "").strip()

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=handlers,
        force=True,
    )

    logging.getLogger(__name__).debug("日志系统已初始化，当前级别：%s", logging.getLevelName(level))


def main():
    _configure_logging()
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--q", type=str, help="The query to search for")
    # args = parser.parse_args()
    from . import server

    asyncio.run(server.main())


__all__ = ["main"]
