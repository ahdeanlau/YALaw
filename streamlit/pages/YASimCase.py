#!/usr/bin/env python3
"""
Scrape every Court-of-Appeal (MYCA) decision on CommonLII,
organising the judgments into ./output/<YEAR>/<slug of case>.txt
"""

import os, re, time, logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm          # progress bar

# ------------------- configuration -------------------

BASE_URL   = "https://www.commonlii.org/my/cases/MYCA/"
OUT_DIR    = Path("output")
SLEEP_SECS = 1.2                              # be polite
HEADERS    = {
    "User-Agent": (
        "MYCA-research-bot/1.0 (+https://example.org/contact; "
        "polite; delays=1.2s)"
    )
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s"
)

# ------------------- helpers -------------------------

slug_re = re.compile(r"[^A-Za-z0-9]+")
def slugify(text: str, limit: int = 150) -> str:
    return slug_re.sub("_", text).strip("_")[:limit]

def fetch(url: str) -> BeautifulSoup:
    """GET a URL and return a BeautifulSoup DOM object."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

# ------------------- step 1: discover years ----------

def discover_year_urls() -> list[tuple[str, str]]:
    """
    Return [(YYYY, full_url), ...] by parsing the MYCA landing page.
    """
    soup = fetch(BASE_URL)
    year_links = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if re.fullmatch(r"\d{4}/?", href):
            full = urljoin(BASE_URL, href)
            year = href.strip("/")

            # filter out duplicates (anchors appear twice on the page)
            if (year, full) not in year_links:
                year_links.append((year, full))

    logging.info("Found %d year folders.", len(year_links))
    return year_links

# ------------------ step 2: discover cases per year ---

def discover_case_links(year_url: str) -> list[tuple[str, str]]:
    """
    For a given /YYYY/ page return [(case_title, case_url), ...]
    """
    soup = fetch(year_url)

    # Every decision link lives in an <a> whose href ends with ".html"
    cases = []
    for a in soup.select("a[href$='.html']"):
        title = a.get_text(strip=True)
        full  = urljoin(year_url, a["href"])

        # Avoid index links like 'index.html' that some folders contain
        if not re.search(r"/index\.html?$", full, re.I):
            cases.append((title, full))
    return cases

# ------------------ step 3: download one judgment -----

def scrape_case(case_title: str, case_url: str, year_dir: Path) -> None:
    """
    Save the entire visible text of `case_url` into a .txt file
    located at   ./output/<YEAR>/<slug>.txt
    """
    outfile = year_dir / f"{slugify(case_title)}.txt"
    if outfile.exists():
        return                         # already scraped this case

    soup = fetch(case_url)

    # Most CommonLII pages are bare <body>.get_text() is fine
    # but trim multiple blank lines:
    text = "\n".join(
        line.strip()
        for line in soup.get_text("\n").splitlines()
        if line.strip()
    )

    outfile.write_text(
        f"{case_title}\n{case_url}\n\n{text}",
        encoding="utf-8"
    )
    time.sleep(SLEEP_SECS)

# ------------------ main orchestration ----------------

def main() -> None:
    for year, year_url in discover_year_urls():
        year_dir = OUT_DIR / year
        year_dir.mkdir(parents=True, exist_ok=True)

        cases = discover_case_links(year_url)
        logging.info("%s: %d cases", year, len(cases))

        for title, url in tqdm(cases, desc=year, unit="case"):
            try:
                scrape_case(title, url, year_dir)
            except Exception as e:
                logging.error("❌  %s\n    %s", url, e)

if __name__ == "__main__":
    main()
