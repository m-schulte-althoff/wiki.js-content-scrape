"""Tests for src.scraper helper functions (no network required)."""

from pathlib import Path

from src.scraper import _base_url, _sanitize_filename, rewrite_media_paths


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


def test_rewrite_media_paths_rewrites_src(tmp_path: Path) -> None:
    """Image src pointing to a local media file is rewritten."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "chart.png").write_bytes(b"fake")

    html = '<img src="/screenshots/chart.png">'
    result = rewrite_media_paths(html, media_dir)
    assert result == '<img src="media/chart.png">'


def test_rewrite_media_paths_rewrites_href(tmp_path: Path) -> None:
    """Document href pointing to a local media file is rewritten."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "report.pdf").write_bytes(b"fake")

    html = '<a href="/docs/report.pdf">Download</a>'
    result = rewrite_media_paths(html, media_dir)
    assert result == '<a href="media/report.pdf">Download</a>'


def test_rewrite_media_paths_leaves_unknown(tmp_path: Path) -> None:
    """References to files NOT in media/ are left unchanged."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    html = '<img src="/missing.png">'
    result = rewrite_media_paths(html, media_dir)
    assert result == html
