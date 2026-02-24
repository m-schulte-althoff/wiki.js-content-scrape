"""Wiki.js content scraper — login, discover pages, download content + media."""

import logging
import re
import urllib.parse
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _select_ldap_strategy(page: Page) -> None:
    """Select the 'LDAP / Active Directory' authentication strategy."""
    # wiki.js login page has a strategy picker; click the LDAP option
    strategy_btn = page.locator("text=LDAP / Active Directory")
    strategy_btn.wait_for(state="visible", timeout=15_000)
    strategy_btn.click()
    logger.info("Selected LDAP / Active Directory strategy")


def login(page: Page, url: str, user: str, password: str) -> None:
    """Navigate to *url*, pick LDAP strategy, fill credentials, submit."""
    logger.info("Navigating to login page: %s", url)
    page.goto(url, wait_until="networkidle", timeout=30_000)

    _select_ldap_strategy(page)

    # Fill credentials
    page.fill('input[type="text"], input#loginUsername, input[autocomplete="username"]', user)
    page.fill('input[type="password"]', password)
    logger.info("Credentials entered for user=%s", user)

    # Click "Anmeldung" button
    page.click('button:has-text("Anmeldung")')
    # Wait for navigation away from login page
    page.wait_for_url(lambda u: "/login" not in u, timeout=30_000)
    logger.info("Login successful — current URL: %s", page.url)


# ---------------------------------------------------------------------------
# Page discovery
# ---------------------------------------------------------------------------

def _base_url(login_url: str) -> str:
    """Derive site base URL from the login URL (strip /login path)."""
    parsed = urllib.parse.urlparse(login_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def discover_pages(page: Page, login_url: str) -> list[str]:
    """Return a sorted, deduplicated list of wiki page URLs.

    Uses the wiki.js GraphQL API (``/graphql``) which every wiki.js v2
    instance exposes once authenticated.  Falls back to crawling sidebar
    links if the API call fails.
    """
    base = _base_url(login_url)
    urls: set[str] = set()

    # --- attempt 1: GraphQL list ---
    try:
        resp = page.evaluate(
            """async (base) => {
                const r = await fetch(base + '/graphql', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: '{ pages { list { id path title } } }'
                    })
                });
                return await r.json();
            }""",
            base,
        )
        pages_list = resp.get("data", {}).get("pages", {}).get("list", [])
        for p in pages_list:
            path = p.get("path", "")
            if path:
                urls.add(f"{base}/{path}")
        if urls:
            logger.info("GraphQL discovery found %d pages", len(urls))
    except Exception:
        logger.warning("GraphQL page list failed — falling back to link crawl")

    # --- attempt 2: sidebar / anchor crawl ---
    if not urls:
        urls = _crawl_sidebar_links(page, base)

    sorted_urls = sorted(urls)
    logger.info("Total pages discovered: %d", len(sorted_urls))
    return sorted_urls


def _crawl_sidebar_links(page: Page, base: str) -> set[str]:
    """Extract internal wiki page links from the current page DOM."""
    # Navigate to home first
    page.goto(base, wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(3000)

    raw_hrefs: list[str] = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => e.href)",
    )
    internal: set[str] = set()
    for href in raw_hrefs:
        parsed = urllib.parse.urlparse(href)
        # keep only same-host, non-login, non-anchor, non-special paths
        if parsed.netloc and parsed.netloc != urllib.parse.urlparse(base).netloc:
            continue
        path = parsed.path.rstrip("/")
        if not path or path in ("/login", "/register", "/favicon.ico"):
            continue
        if re.match(r"^/(_|graphql|healthz|a/)", path):
            continue
        full = f"{base}{path}"
        internal.add(full)
    logger.info("Link-crawl discovered %d internal pages", len(internal))
    return internal


# ---------------------------------------------------------------------------
# Content + media download
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """Replace filesystem-unfriendly characters."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def save_page(page: Page, url: str, out_dir: Path) -> Path:
    """Save a single wiki page's content and inline media to *out_dir*.

    Returns the path to the saved HTML file.
    """
    logger.info("Saving page: %s", url)
    page.goto(url, wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(2000)

    # Derive a filename from the page title or URL path
    title = page.title() or urllib.parse.urlparse(url).path.strip("/").replace("/", "_")
    safe_title = _sanitize_filename(title)

    page_dir = out_dir / safe_title
    page_dir.mkdir(parents=True, exist_ok=True)

    # --- download media (images, PDFs, etc.) ---
    media_dir = page_dir / "media"
    media_dir.mkdir(exist_ok=True)
    _download_media(page, media_dir)

    # --- snapshot the HTML content ---
    content_el = page.query_selector(".contents, .page-content, #page-content, article, main")
    html = content_el.inner_html() if content_el else page.content()

    html_path = page_dir / f"{safe_title}.html"
    html_path.write_text(html, encoding="utf-8")
    logger.info("Saved HTML → %s", html_path)
    return html_path


def _download_media(page: Page, media_dir: Path) -> None:
    """Download images and linked media files referenced on the page."""
    base = f"{urllib.parse.urlparse(page.url).scheme}://{urllib.parse.urlparse(page.url).netloc}"

    # Collect image sources
    srcs: list[str] = page.eval_on_selector_all(
        "img[src]",
        "els => els.map(e => e.src)",
    )
    # Collect linked documents (pdf, docx, etc.)
    hrefs: list[str] = page.eval_on_selector_all(
        'a[href$=".pdf"], a[href$=".docx"], a[href$=".xlsx"], '
        'a[href$=".pptx"], a[href$=".zip"], a[href$=".csv"]',
        "els => els.map(e => e.href)",
    )
    all_urls = set(srcs + hrefs)
    downloaded = 0

    for media_url in all_urls:
        if not media_url or media_url.startswith("data:"):
            continue
        # Make absolute
        if media_url.startswith("/"):
            media_url = base + media_url
        try:
            resp = page.request.get(media_url, timeout=15_000)
            if resp.ok:
                fname = _sanitize_filename(
                    urllib.parse.unquote(urllib.parse.urlparse(media_url).path.split("/")[-1])
                )
                if not fname:
                    continue
                dest = media_dir / fname
                dest.write_bytes(resp.body())
                downloaded += 1
        except Exception as exc:
            logger.warning("Failed to download %s: %s", media_url, exc)

    logger.info("Downloaded %d media files to %s", downloaded, media_dir)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def scrape_wiki(
    login_url: str,
    user: str,
    password: str,
    wiki_name: str = "IMI Wiki",
) -> Path:
    """Full pipeline: login → discover → save all pages + media.

    Returns the output directory.
    """
    out_dir = DATA_DIR / wiki_name
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", out_dir)

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=True)
        context: BrowserContext = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 900},
        )
        context.set_default_timeout(60_000)
        context.set_default_navigation_timeout(60_000)
        pg: Page = context.new_page()

        login(pg, login_url, user, password)

        urls = discover_pages(pg, login_url)
        if not urls:
            logger.warning("No pages discovered — saving home page only")
            base = _base_url(login_url)
            urls = [base]

        saved = 0
        for i, url in enumerate(urls, 1):
            try:
                save_page(pg, url, out_dir)
                saved += 1
                logger.info("Progress: %d/%d pages saved", saved, len(urls))
            except Exception as exc:
                logger.error("Error saving %s (%d/%d): %s", url, i, len(urls), exc)

        browser.close()

    logger.info("Scraping complete — %d/%d pages saved to %s", saved, len(urls), out_dir)
    return out_dir
