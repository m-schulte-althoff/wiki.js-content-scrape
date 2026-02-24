"""Main controller — entry point for the wiki.js scraper pipeline."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from src.config import load_config
from src.scraper import scrape_wiki

LOGS_DIR = Path(__file__).resolve().parent / "logs"


def _setup_logging() -> None:
    """Configure root logger to write to stdout and a timestamped log file."""
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"scrape_{ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    logging.getLogger(__name__).info("Log file: %s", log_file)


def run_scrape() -> None:
    """Load config and run the scrape pipeline."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    config = load_config()
    logger.info("Starting scrape for page=%s", config["page"])

    out = scrape_wiki(
        login_url=config["page"],
        user=config["user"],
        password=config["password"],
        wiki_name="IMI Wiki",
    )
    logger.info("Pipeline finished — output at %s", out)


def main() -> None:
    """CLI dispatcher."""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scrape"
    if cmd == "scrape":
        run_scrape()
    else:
        print(f"Unknown command: {cmd}. Usage: python3 main.py scrape")
        sys.exit(1)


if __name__ == "__main__":
    main()
