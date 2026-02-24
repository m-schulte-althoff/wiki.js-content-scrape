"""Tests for src.scraper helper functions (no network required)."""

from src.scraper import _base_url, _sanitize_filename


def test_base_url_strips_path() -> None:
    """_base_url removes the path and returns scheme + netloc."""
    assert _base_url("https://wiki.example.com/login") == "https://wiki.example.com"


def test_base_url_preserves_port() -> None:
    """_base_url keeps port numbers."""
    assert _base_url("http://localhost:3000/login") == "http://localhost:3000"


def test_sanitize_filename_replaces_special_chars() -> None:
    """Filesystem-unfriendly characters are replaced with underscores."""
    assert _sanitize_filename('page:"hello"/world') == "page__hello__world"


def test_sanitize_filename_strips_whitespace() -> None:
    """Leading/trailing whitespace is stripped."""
    assert _sanitize_filename("  hello  ") == "hello"
