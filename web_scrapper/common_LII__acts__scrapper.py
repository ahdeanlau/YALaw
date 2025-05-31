#!/usr/bin/env python3
"""
Scraper for **Malaysian Consolidated Legislation** on CommonLII.

It walks every year listed on the landing page and downloads the HTML for each
Act into   ./output_acts/<YEAR>/<slugified-title>.html

The script is stand-alone and does **not** include the MYCA judgment probe.

Usage
-----
$ python commonlii_acts_scraper.py

Configuration values live in the CONFIG section at the top – adjust years,
request delay, or output folder as needed.
"""
from __future__ import annotations

import logging, time, re, unicodedata
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

# ═════════════════════════════════ CONFIG ════════════════════════════════════
BASE_URL: str = "https://www.commonlii.org/my/legis/consol_act/"  # must end /
START_YEAR: int = 1914
END_YEAR:   int = 2006  # last year on landing page
SLEEP: float = 2.0       # seconds between requests – be polite!
REQUEST_TIMEOUT: int = 60
OUT_DIR: Path = Path("output_acts")
VERIFY_SSL: bool = False  # set True if your CA bundle is fixed (see README)
HEADERS: Dict[str, str] = {
    "User-Agent": "MY-Acts-Scraper/1.0 (+mailto:you@example.com)"
}
LOG_LEVEL = logging.INFO
# ═════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level   = LOG_LEVEL,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)

session = requests.Session()

# ────────────────────────────── helpers ──────────────────────────────────────

def slugify(text: str, max_len: int = 150) -> str:
    """Filesystem-safe ASCII slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return text[:max_len] or "untitled"

def get(url: str) -> requests.Response:
    logging.debug("GET %s", url)
    return session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)

# ────────────────────────────── scraper logic ────────────────────────────────

def fetch_year_links() -> Dict[int, str]:
    """Return {year: href} by parsing the landing page."""
    landing = get(BASE_URL)
    landing.raise_for_status()
    soup = BeautifulSoup(landing.text, "html.parser")
    links = {}
    for a in soup.select("a[href^='toc-'][href$='.html']"):
        year_txt = a.text.strip()
        if year_txt.isdigit():
            links[int(year_txt)] = a["href"]
    return links

def scrape_act(year: int, title: str, href: str) -> None:
    act_url = href if href.startswith("http") else BASE_URL + href
    if not act_url.endswith(('.html', '/')):
        act_url += '/'  # ensure directory links load index page

    logging.info("Fetching act: %s (%s)", title, act_url)
    try:
        resp = get(act_url)
    except requests.RequestException as e:
        logging.warning("Network error %s", e)
        return
    if resp.status_code != 200:
        logging.warning("HTTP %d for %s", resp.status_code, act_url)
        return

    year_dir = OUT_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    file_path = year_dir / f"{slugify(title)}.html"
    file_path.write_text(resp.text, encoding="utf-8")
    logging.info("✅ saved → %s", file_path)


def main() -> None:
    # Discover year links
    year_links = fetch_year_links()
    logging.info("Landing page lists %d year buckets", len(year_links))

    for year in range(START_YEAR, END_YEAR + 1):
        href = year_links.get(year)
        if not href:
            logging.info("Year %d missing – skipping", year)
            continue

        toc_url = href if href.startswith("http") else BASE_URL + href
        logging.info("Year %d → TOC %s", year, toc_url)
        try:
            toc_resp = get(toc_url)
        except requests.RequestException as e:
            logging.warning("Network error TOC %s", e)
            continue
        if toc_resp.status_code != 200:
            logging.warning("TOC HTTP %d", toc_resp.status_code)
            continue

        toc_soup = BeautifulSoup(toc_resp.text, "html.parser")
        act_links: List[BeautifulSoup] = toc_soup.select("li > a[href]")
        logging.info("Found %d acts for %d", len(act_links), year)

        for a in act_links:
            title = a.get_text(strip=True) or "untitled"
            scrape_act(year, title, a["href"])
            time.sleep(SLEEP)

    logging.info("All done – legislation scrape finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Interrupted by user – exiting.")
