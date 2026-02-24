# wiki.js Content Scraper

Automated scraper for wiki.js instances. Logs in via LDAP / Active Directory, discovers all pages through the GraphQL API, and saves each page's HTML content plus media files locally.

## How to Reproduce

1. **Install dependencies** (requires [uv](https://docs.astral.sh/uv/)):
   ```bash
   uv sync
   uv run playwright install chromium
   ```

2. **Configure** `.env` in the project root:
   ```
   page = "https://your-wiki.example.com/login"
   user = "YOUR_USERNAME"
   password = "YOUR_PASSWORD"
   ```

3. **Run the scraper**:
   ```bash
   uv run python3 main.py scrape
   ```

4. **Check output** in `data/IMI Wiki/` — one subfolder per page with HTML + media.

## Data Sources

- Wiki.js instance at the URL specified in `.env`
- Authentication via LDAP / Active Directory
- Page discovery via wiki.js GraphQL API (`/graphql`)

## File Structure

```
├── main.py              # Controller — CLI entry point
├── views.py             # View module (placeholder)
├── pyproject.toml       # Project config (deps, ruff, mypy, pytest)
├── .env                 # Credentials (not committed)
├── src/
│   ├── config.py        # .env loader + validation
│   └── scraper.py       # Core scraping logic (login, discover, save)
├── data/
│   └── IMI Wiki/        # Scraped pages (HTML + media per page)
├── logs/                # Timestamped log files
├── output/
│   ├── tables/
│   └── figures/
└── tests/
    ├── test_config.py
    └── test_scraper_helpers.py
```

## Development

```bash
uv run pytest -q                          # run all tests
uv run pytest -q tests/test_config.py     # single module
uv run ruff check .                       # lint
uv run mypy .                             # type check
```
