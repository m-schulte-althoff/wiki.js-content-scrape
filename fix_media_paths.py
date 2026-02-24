"""One-time script: rewrite media paths in all existing scraped HTML files.

Usage:
    uv run python3 fix_media_paths.py
"""

import logging
import sys
from pathlib import Path

from src.scraper import rewrite_media_paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data" / "IMI Wiki"


def fix_all() -> None:
    """Rewrite media references in every HTML file under data/IMI Wiki/."""
    if not DATA_DIR.exists():
        logger.error("Data directory not found: %s", DATA_DIR)
        sys.exit(1)

    html_files = sorted(DATA_DIR.rglob("*.html"))
    logger.info("Found %d HTML files to patch", len(html_files))
    patched = 0

    for html_path in html_files:
        media_dir = html_path.parent / "media"
        if not media_dir.exists():
            continue

        original = html_path.read_text(encoding="utf-8")
        rewritten = rewrite_media_paths(original, media_dir)

        if rewritten != original:
            html_path.write_text(rewritten, encoding="utf-8")
            patched += 1
            logger.info("Patched: %s", html_path.name)

    logger.info("Done — %d/%d files patched", patched, len(html_files))


if __name__ == "__main__":
    fix_all()
