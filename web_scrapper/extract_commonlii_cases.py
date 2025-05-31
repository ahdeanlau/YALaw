"""extract_commonlii_cases.py

Walk through the CommonLII HTML dumps stored under the local
`output_probe/` folder and generate a `.json` file alongside each
`.html` judgment that captures rich metadata for downstream RAG / search
pipelines.

Captured fields (set to **null** if not found):

| JSON key              | Example value (Ho Lai Ying v Cempaka)                                   | How we get it                               |
|-----------------------|---------------------------------------------------------------------------|---------------------------------------------|
| case_name            | "Ho Lai Ying & Kor Toong Khoon v Cempaka Finance Bhd"                     | `<title>` / first `<h2>`                    |
| neutral_citation     | "[1999] MYCA 3"                                                           | regex on `<title>`                          |
| case_number          | "W-03-151-2000"                                                           | regex on `<title>`                          |
| decision_date        | "1999-04-19"                                                              | `<!--sino date …-->` or date in title       |
| court                | "Court of Appeal of Malaysia"                                            | first `<h1>`                                |
| coram                | "Alauddin Mohd Sheriff JCA; Mohd Ghazali Mohd Yusoff JCA; Abdul Malik Ishak HMT" | text block after the word "CORAM"          |
| appellants           | "Ho Lai Ying (trading as K.H. Trading); Kor Toong Khoon"                  | block containing "PERAYU" / "APPELLANT"    |
| respondents          | "Cempaka Finance Berhad"                                                  | block containing "RESPONDEN" / "RESPONDENT"|
| counsel_appellant    | "S.L. Tan – Tetuan S L Tan & Associates"                                  | "For the appellants:" section              |
| counsel_respondent   | "Nadrah bte Mohamed – Tetuan Shatar Tan & Chee"                           | "For the respondent:" section              |
| outcome              | "Appeal allowed with costs" (free text)                                   | heuristic search near end of judgment       |
| source_html_file     | relative path to originating HTML                                          |                                             |
| full_text            | full cleaned body text                                                     |                                             |

Run with:

```bash
python extract_commonlii_cases.py              # default ./output_probe/commonlii__myca
python extract_commonlii_cases.py /some/root   # custom dump location
```

Requires `beautifulsoup4` and `lxml`.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from bs4 import BeautifulSoup, Comment, NavigableString

# ────────────────────────────────────────────────────────────────────────────────
# Regex helpers
# ────────────────────────────────────────────────────────────────────────────────
DATE_RE = re.compile(r"([0-9]{1,2})\s+([A-Za-z]+)\s+([0-9]{4})")
TITLE_CITATION_RE = re.compile(
    r"^(?P<case>.*?)\s+-.*?\[(?P<year>[0-9]{4})\]\s+(?P<series>[A-Z]+)\s+(?P<number>[0-9]+)",
    re.DOTALL,
)
CASE_NUMBER_RE = re.compile(r"\b([A-Z]-\s*\d+-\d+-\d+)\b")

MONTHS = {m: i for i, m in enumerate(
    [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    start=1,
)}

OUTCOME_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"appeal\s+allowed(?:\s+with\s+costs)?",
        r"appeal\s+dismissed(?:\s+with\s+costs)?",
        r"application\s+is\s+granted",
        r"application\s+is\s+dismissed",
    ]
]

# ────────────────────────────────────────────────────────────────────────────────
# Utility functions
# ────────────────────────────────────────────────────────────────────────────────

def _parse_date(text: str) -> Optional[str]:
    match = DATE_RE.search(text)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = MONTHS.get(month_name)
    if not month:
        return None
    try:
        dt = datetime(int(year), month, int(day))
        return dt.date().isoformat()
    except ValueError:
        return None


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# ────────────────────────────────────────────────────────────────────────────────
# Core extraction
# ────────────────────────────────────────────────────────────────────────────────

def extract_metadata(html_path: Path) -> Dict[str, Optional[str]]:
    """Parse a CommonLII HTML file and return rich metadata."""

    with html_path.open("r", encoding="utf‑8", errors="replace") as fh:
        soup = BeautifulSoup(fh, "lxml")

    title_text = soup.title.string.strip() if soup.title and soup.title.string else ""

    case_name = neutral_citation = None
    m = TITLE_CITATION_RE.search(title_text)
    if m:
        case_name = _collapse_ws(m.group("case"))
        neutral_citation = f"[{m.group('year')}] {m.group('series')} {m.group('number')}"

    # case number
    case_number = None
    m = CASE_NUMBER_RE.search(title_text)
    if m:
        case_number = _collapse_ws(m.group(1))

    # decision date from sino comment → title fallback
    decision_date = None
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if "sino date" in comment.lower():
            decision_date = _parse_date(comment)
            if decision_date:
                break
    if not decision_date:
        decision_date = _parse_date(title_text)

    # court (first <h1>)
    h1 = soup.find("h1")
    court = h1.get_text(strip=True) if h1 else None

    # full_text – concatenate visible text inside each Section div + loose <p>
    body_text_parts: list[str] = []
    for div in soup.select("div[class^=Section]"):
        body_text_parts.append(div.get_text(" ", strip=True))
    # fallback if no Section divs
    if not body_text_parts:
        body_text_parts.append(soup.body.get_text(" ", strip=True) if soup.body else "")
    full_text = _collapse_ws("\n".join(body_text_parts)) or None

    # coram: look for the word CORAM in any tag, grab following text (next 300 chars)
    coram = None
    coram_tag = soup.find(string=re.compile(r"coram", re.I))
    if coram_tag:
        snippet = "".join(coram_tag.find_parent().stripped_strings)
        after = _collapse_ws(snippet.split(":", 1)[-1])
        coram = after if after else None

    # parties blocks (appellants / respondents)
    appellants = respondents = None
    party_block = soup.find(string=re.compile(r"PERAYU|APPELLANT", re.I))
    if party_block:
        appellants = _collapse_ws(party_block.find_parent().get_text(" ", strip=True))
    resp_block = soup.find(string=re.compile(r"RESPONDEN|RESPONDENT", re.I))
    if resp_block:
        respondents = _collapse_ws(resp_block.find_parent().get_text(" ", strip=True))

    # counsel lines – very consistent labels
    def _extract_counsel(label_re: re.Pattern[str]) -> Optional[str]:
        tag = soup.find(string=label_re)
        if not tag:
            return None
        texts: list[str] = []
        # grab subsequent <p> siblings until we hit an empty line or another "For the" label
        for sib in tag.parent.next_siblings:
            if isinstance(sib, NavigableString):
                continue
            if sib.name and sib.get_text(strip=True):
                if re.search(r"^for the", sib.get_text(strip=True), re.I):
                    break
                texts.append(sib.get_text(" ", strip=True))
            if len(texts) >= 2:
                break
        return _collapse_ws("; ".join(texts)) if texts else None

    counsel_appellant = _extract_counsel(re.compile(r"for the appellants?", re.I))
    counsel_respondent = _extract_counsel(re.compile(r"for the respondent", re.I))

    # outcome – scan last 20 lines for common phrases
    outcome = None
    if full_text:
        tail = full_text[-2000:].lower()
        for pat in OUTCOME_PATTERNS:
            m = pat.search(tail)
            if m:
                outcome = _collapse_ws(m.group(0).capitalize())
                break

    # path relative to project root if possible
    try:
        project_root = Path(__file__).resolve().parent.parent
        src_path = str(html_path.resolve().relative_to(project_root))
    except ValueError:
        src_path = str(html_path.resolve())

    return {
        "case_name": case_name,
        "neutral_citation": neutral_citation,
        "case_number": case_number,
        "decision_date": decision_date,
        "court": court,
        "coram": coram,
        "appellants": appellants,
        "respondents": respondents,
        "counsel_appellant": counsel_appellant,
        "counsel_respondent": counsel_respondent,
        "outcome": outcome,
        "source_html_file": src_path,
        "full_text": full_text,
    }

# ────────────────────────────────────────────────────────────────────────────────
# CLI driver
# ────────────────────────────────────────────────────────────────────────────────

def main(root: Path) -> None:
    html_files = sorted(root.rglob("*.html"))
    if not html_files:
        print(f"No HTML files found under {root}")
        return

    project_root = Path(__file__).resolve().parent.parent

    for html_path in html_files:
        meta = extract_metadata(html_path)
        json_path = html_path.with_suffix(".json")
        with json_path.open("w", encoding="utf‑8") as fp:
            json.dump(meta, fp, ensure_ascii=False, indent=2)
        try:
            rel = json_path.resolve().relative_to(project_root)
            print(f"✓ {rel}")
        except ValueError:
            print(f"✓ {json_path.resolve()}")

if __name__ == "__main__":
    root_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output_probe/commonlii__myca")
    if not root_dir.exists():
        print(f"The directory '{root_dir}' does not exist.")
        sys.exit(1)
    main(root_dir)
