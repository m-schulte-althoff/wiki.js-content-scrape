"""Tests for src.config module."""

from pathlib import Path

import pytest

from src.config import load_config


def test_load_config_valid(tmp_path: Path) -> None:
    """Config loads correctly from a well-formed .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        'page = "https://example.com/login"\n'
        'user = "alice"\n'
        'password = "s3cret"\n'
    )
    cfg = load_config(env_path=env_file)
    assert cfg["page"] == "https://example.com/login"
    assert cfg["user"] == "alice"
    assert cfg["password"] == "s3cret"


def test_load_config_missing_key(tmp_path: Path) -> None:
    """Config raises ValueError when a required key is missing."""
    env_file = tmp_path / ".env"
    env_file.write_text('page = "https://example.com/login"\nuser = "bob"\n')
    with pytest.raises(ValueError, match="password"):
        load_config(env_path=env_file)


def test_load_config_empty_file(tmp_path: Path) -> None:
    """Config raises ValueError for an empty .env."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    with pytest.raises(ValueError):
        load_config(env_path=env_file)
