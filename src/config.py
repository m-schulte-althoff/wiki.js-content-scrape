"""Configuration loader — reads .env and exposes wiki credentials."""

import logging
from pathlib import Path

from dotenv import dotenv_values

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_config(env_path: Path = _ENV_PATH) -> dict[str, str]:
    """Load and validate required env variables (page, user, password).

    Returns a dict with keys ``page``, ``user``, ``password``.
    """
    raw = dotenv_values(env_path)
    required_keys = ("page", "user", "password")
    missing = [k for k in required_keys if not raw.get(k)]
    if missing:
        raise ValueError(f"Missing required .env variables: {missing}")
    config: dict[str, str] = {k: raw[k] for k in required_keys}  # type: ignore[misc]
    logger.info("Config loaded — page=%s, user=%s", config["page"], config["user"])
    return config
