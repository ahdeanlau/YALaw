#!/usr/bin/env python3
"""
Probe‑style scraper for CommonLII MYCA judgments when index pages are 410 (no directory listing).

⚠️  /my/cases/ is disallowed in robots.txt.  Set ALLOW_DISALLOWED=True **only** if you have
    explicit written permission from the site owner.

Edit the *configuration* block below to change years, max document number, etc.
"""

from __future__ import annotations

import time, logging
from pathlib import Path
from typing import Iterator

import requests
# If you fix your CA bundle, switch verify=False → verify=certifi.where().
# import certifi

# ────────────────────────────── configuration ────────────────────────────────
BASE_DIR: str      = "https://www.commonlii.org/my/cases/MYSSHC/"  # trailing slash required
START_YEAR: int    = 2005   # inclusive
END_YEAR: int      = 2012   # inclusive
MAX_DOC_NO: int    = 999    # highest document index to try per year
MAX_CONSEC_MISSES: int = 3 # after n consecutive 404s, assume the year is done
REQUEST_TIMEOUT: int = 60   # seconds before we give up waiting for a response
SLEEP: float       = 1.2    # polite delay between requests (seconds)
ALLOW_DISALLOWED: bool = True  # flip to False unless you truly have permission

OUT_DIR: Path      = Path("output_probe/commonlii__mysshc")
HEADERS: dict[str, str] = {
    "User-Agent": "MYCA-probe/0.2 (+mailto:you@example.com)"
}
LOG_LEVEL: int = logging.INFO
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level   = LOG_LEVEL,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)

Session = requests.Session  # alias for type hints


def years() -> Iterator[int]:
    """Generate each year in the configured window (inclusive)."""
    yield from range(START_YEAR, END_YEAR + 1)


def grab(session: Session, url: str) -> requests.Response:
    """Single GET request with timeout. Caller handles status_code."""
    logging.debug("GET %s", url)
    resp = session.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        verify=False,  # change to certifi.where() if using proper certs
    )
    return resp


def save_html(text: str, year: int, doc_no: int) -> None:
    """Write raw HTML to ./output_probe/<year>/<doc_no>.html"""
    p = OUT_DIR / str(year)
    p.mkdir(parents=True, exist_ok=True)
    outfile = p / f"{doc_no}.html"
    outfile.write_text(text, encoding="utf-8")
    logging.debug("saved → %s", outfile)


def main() -> None:
    if not ALLOW_DISALLOWED:
        logging.error(
            "robots.txt disallows /my/cases/.  Aborting.\n"
            "Flip ALLOW_DISALLOWED=True only if you have permission."
        )
        return

    session = requests.Session()

    for year in years():
        logging.info("──────── Year %d ────────", year)
        consecutive_misses = 0

        for doc in range(1, MAX_DOC_NO + 1):
            url = f"{BASE_DIR}{year}/{doc}.html"
            logging.info("Attempt: year=%d, doc=%d", year, doc)
            try:
                r = grab(session, url)
            except requests.RequestException as e:
                logging.warning("Network error → %s", e)
                time.sleep(SLEEP)
                continue

            if r.status_code == 200:
                save_html(r.text, year, doc)
                logging.info("✅ 200 OK → saved (%d/%d)", year, doc)
                consecutive_misses = 0

            elif r.status_code == 404:
                consecutive_misses += 1
                logging.info("404 not found (%d/%d) [%d consecutive]", year, doc, consecutive_misses)

                if consecutive_misses >= MAX_CONSEC_MISSES:
                    logging.info("Reached %d consecutive 404s – stopping year %d", MAX_CONSEC_MISSES, year)
                    break

            else:
                logging.warning("⚠️ %s → HTTP %d", url, r.status_code)

            time.sleep(SLEEP)

    logging.info("Finished all years.")


if __name__ == "__main__":
    main()
