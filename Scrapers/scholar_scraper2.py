"""
Scrapers/scholarship_scraper.py
--------------------------------
Scrapes scholarship listings from:
  1. Scholars4Dev    (https://www.scholars4dev.com)
  2. ScholarshipPositions (https://scholarshippositions.com)

Falls back to 20 curated seed scholarships if live scraping fails.

Usage:
    python scholarship_scraper.py          # live scraping
    python scholarship_scraper.py --seed   # seed data only (fast)
"""

import csv
import sys
import time
import logging
import re
import random
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DATA_DIR   = Path(__file__).parent.parent / "Data"
OUTPUT_CSV = DATA_DIR / "scholarships_raw.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
}

CSV_FIELDS = [
    "id", "title", "host_country", "host_university", "degree_level",
    "field_of_study", "deadline", "amount", "eligibility", "description",
    "url", "source", "scraped_at",
]

# ── helpers ────────────────────────────────────────────────────────────────

def _get(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as exc:
            log.warning("Attempt %d failed for %s: %s", attempt + 1, url, exc)
            time.sleep(2 ** attempt + random.uniform(0, 1))
    return None

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

# ── field extractors ───────────────────────────────────────────────────────

_COUNTRY_KEYWORDS = [
    "USA", "United States", "UK", "United Kingdom", "Canada", "Australia",
    "Germany", "France", "Netherlands", "Japan", "China", "Sweden",
    "Norway", "Finland", "South Korea", "Switzerland", "Belgium", "Italy",
    "New Zealand", "Ireland", "Austria", "Denmark", "Turkey", "India",
    "Ethiopia", "Kenya", "Nigeria", "Ghana", "South Africa",
]

_DEGREE_MAP = {
    r"\bPhD\b|doctoral|doctorate":               "PhD",
    r"\bmaster'?s?\b|MSc|MA\b|MBA|MEng":        "Master's",
    r"\bbachelor'?s?\b|undergrad|BSc|BA\b":      "Bachelor's",
    r"\bpostdoc\b|post-doc":                      "Postdoctoral",
    r"\bshort.?course|certificate|diploma":       "Certificate/Diploma",
}

_FIELD_KEYWORDS = {
    "STEM":             ["engineering", "science", "technology", "mathematics", "physics", "chemistry", "biology"],
    "Medicine":         ["medicine", "health", "medical", "nursing", "pharmacy", "public health"],
    "Business":         ["business", "economics", "finance", "management", "mba", "commerce"],
    "Arts & Humanities":["humanities", "arts", "literature", "history", "philosophy", "linguistics"],
    "Law":              ["law", "legal", "jurisprudence"],
    "Agriculture":      ["agriculture", "agronomy", "food science", "environmental"],
    "Social Sciences":  ["social", "psychology", "sociology", "political science", "international relations"],
    "Education":        ["education", "teaching", "pedagogy"],
    "IT & Computing":   ["computer", "software", "data science", "artificial intelligence", "machine learning", "ict"],
}

def extract_country(title: str, body: str) -> str:
    combined = (title + " " + body).lower()
    for c in _COUNTRY_KEYWORDS:
        if c.lower() in combined:
            return c
    return "International"

def extract_university(body: str) -> str:
    m = re.search(r"(?:University|Institute|College|School) of [A-Z][a-zA-Z ]+", body)
    if m: return m.group(0)[:80]
    m2 = re.search(r"[A-Z][a-zA-Z]+ University", body)
    return m2.group(0)[:80] if m2 else ""

def extract_degree(text: str) -> str:
    for pattern, label in _DEGREE_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return "Any"

def extract_field(body: str) -> str:
    body_lower = body.lower()
    scores = {f: sum(body_lower.count(k) for k in kws) for f, kws in _FIELD_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Any"

def extract_deadline(body: str) -> str:
    for pat in [
        r"deadline[:\s]+([A-Za-z]+ \d{1,2},? \d{4})",
        r"apply by[:\s]+([A-Za-z]+ \d{1,2},? \d{4})",
        r"closing date[:\s]+([A-Za-z]+ \d{1,2},? \d{4})",
        r"(\d{1,2} [A-Za-z]+ \d{4})",
    ]:
        m = re.search(pat, body, re.IGNORECASE)
        if m: return m.group(1).strip()
    return "See website"

def extract_amount(body: str) -> str:
    m = re.search(
        r"(fully.?funded|full.?scholarship|\$[\d,]+|€[\d,]+|£[\d,]+|[\d,]+ (?:USD|EUR|GBP))",
        body, re.IGNORECASE,
    )
    return m.group(0) if m else "Varies"

# ── scrapers ───────────────────────────────────────────────────────────────

def scrape_scholars4dev(max_pages: int = 5) -> list[dict]:
    base = "https://www.scholars4dev.com"
    results = []
    for page in range(1, max_pages + 1):
        url = base if page == 1 else f"{base}/page/{page}/"
        log.info("[Scholars4Dev] page %d", page)
        soup = _get(url)
        if not soup: break
        articles = soup.select("article.post") or soup.select("div.post")
        if not articles: break
        for art in articles:
            try:
                tag = art.select_one("h2 a") or art.select_one("h1 a")
                if not tag: continue
                title = _clean(tag.get_text())
                link  = tag.get("href", "")
                detail = _get(link) if link else None
                body = ""
                if detail:
                    cnt = detail.select_one("div.entry-content") or detail.select_one("article")
                    body = _clean(cnt.get_text(" ")) if cnt else ""
                results.append(_build_row(f"s4d_{len(results)+1:04d}", title, body, link, "scholars4dev"))
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as exc:
                log.warning("Parse error: %s", exc)
        time.sleep(random.uniform(1, 2.5))
    log.info("[Scholars4Dev] %d scholarships scraped", len(results))
    return results


def scrape_scholarshippositions(max_pages: int = 5) -> list[dict]:
    base = "https://scholarshippositions.com"
    results = []
    for page in range(1, max_pages + 1):
        url = f"{base}/page/{page}/" if page > 1 else base + "/"
        log.info("[ScholarshipPositions] page %d", page)
        soup = _get(url)
        if not soup: break
        posts = soup.select("article") or soup.select("div.post")
        if not posts: break
        for post in posts:
            try:
                tag = post.select_one("h2 a") or post.select_one("h3 a")
                if not tag: continue
                title = _clean(tag.get_text())
                link  = tag.get("href", "")
                ex = post.select_one("div.entry-summary") or post.select_one("p")
                body = _clean(ex.get_text()) if ex else ""
                results.append(_build_row(f"sp_{len(results)+1:04d}", title, body, link, "scholarshippositions"))
                time.sleep(random.uniform(0.3, 1))
            except Exception as exc:
                log.warning("Parse error: %s", exc)
        time.sleep(random.uniform(1, 2))
    log.info("[ScholarshipPositions] %d scholarships scraped", len(results))
    return results


def _build_row(id_: str, title: str, body: str, url: str, source: str) -> dict:
    return {
        "id":             id_,
        "title":          title,
        "host_country":   extract_country(title, body),
        "host_university": extract_university(body),
        "degree_level":   extract_degree(title + " " + body),
        "field_of_study": extract_field(body),
        "deadline":       extract_deadline(body),
        "amount":         extract_amount(body),
        "eligibility":    body[:500],
        "description":    body[:1000],
        "url":            url,
        "source":         source,
        "scraped_at":     datetime.now(timezone.utc).isoformat(),
    }

# ── seed data ──────────────────────────────────────────────────────────────

def _s(id_, title, country, university, degree, field, deadline, amount, eligibility, url):
    return {
        "id": id_, "title": title, "host_country": country,
        "host_university": university, "degree_level": degree,
        "field_of_study": field, "deadline": deadline, "amount": amount,
        "eligibility": eligibility, "description": eligibility,
        "url": url, "source": "seed",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }

SEED_SCHOLARSHIPS = [
    _s("seed_001","Chevening Scholarships","UK","Various UK Universities","Master's","Any","November 2025","Fully Funded","Open to citizens of Chevening-eligible countries with 2+ years work experience.","https://www.chevening.org/scholarships/"),
    _s("seed_002","DAAD Scholarships","Germany","Various German Universities","Master's","STEM","October 2025","Fully Funded","Open to international students for postgraduate studies in Germany.","https://www.daad.de/en/"),
    _s("seed_003","Fulbright Foreign Student Program","USA","Various US Universities","Master's","Any","February 2026","Fully Funded","Open to students from 160+ countries for graduate study in the US.","https://foreign.fulbrightonline.org/"),
    _s("seed_004","Erasmus Mundus Joint Master Degrees","Europe","Multiple European Universities","Master's","Any","January 2026","€1,400/month + tuition","Open to students worldwide for joint master programmes across Europe.","https://www.eacea.ec.europa.eu/scholarships/emjmd_en"),
    _s("seed_005","Commonwealth Scholarships","UK","Various UK Universities","PhD","Any","October 2025","Fully Funded","Open to citizens of Commonwealth countries for PhD study in the UK.","https://cscuk.fcdo.gov.uk/scholarships/"),
    _s("seed_006","Australia Awards Scholarships","Australia","Various Australian Universities","Master's","Any","April 2026","Fully Funded","Open to citizens of eligible developing countries in the Indo-Pacific region.","https://www.dfat.gov.au/people-to-people/australia-awards"),
    _s("seed_007","Gates Cambridge Scholarship","UK","University of Cambridge","PhD","Any","October 2025","Fully Funded","Open to international students for postgraduate study at Cambridge.","https://www.gatescambridge.org/"),
    _s("seed_008","Swedish Institute Scholarships (SISGP)","Sweden","Various Swedish Universities","Master's","Social Sciences","February 2026","SEK 11,000/month","Open to citizens of specific countries with leadership potential and work experience.","https://si.se/en/apply/scholarships/"),
    _s("seed_009","Mastercard Foundation Scholars Program","USA","Multiple Partner Universities","Bachelor's","Any","March 2026","Fully Funded","Open to academically talented yet economically disadvantaged students from Africa.","https://mastercardfdn.org/all/scholars/"),
    _s("seed_010","Japanese Government MEXT Scholarship","Japan","Various Japanese Universities","Master's","Any","May 2026","Fully Funded","Open to students from countries with diplomatic relations with Japan.","https://www.mext.go.jp/en/"),
    _s("seed_011","Korean Government Scholarship (KGSP)","South Korea","Various Korean Universities","Master's","Any","March 2026","Fully Funded","Open to international students from countries with diplomatic relations with Korea.","https://www.studyinkorea.go.kr/"),
    _s("seed_012","ETH Zürich Excellence Scholarship","Switzerland","ETH Zürich","Master's","STEM","December 2025","CHF 12,000/semester","Open to outstanding students applying for master's programmes at ETH Zürich.","https://ethz.ch/en/studies/financial/scholarships/excellencescholarship.html"),
    _s("seed_013","Heinrich Böll Foundation Scholarships","Germany","Various German Universities","PhD","Social Sciences","March 2026","€934/month","Open to students committed to ecology, democracy, solidarity and non-violence.","https://www.boell.de/en/foundation/scholarships"),
    _s("seed_014","Rotary Peace Fellowships","International","Rotary Peace Centers","Master's","Social Sciences","May 2026","Fully Funded","Open to experienced professionals committed to peace and development.","https://www.rotary.org/en/our-programs/peace-fellowships"),
    _s("seed_015","AfDB Coding for Employment Scholarship","Africa","Partner Institutions","Certificate/Diploma","IT & Computing","Rolling","Varies","Open to African youth interested in digital skills and coding.","https://www.afdb.org/"),
    _s("seed_016","Rhodes Scholarship – Oxford","UK","University of Oxford","Master's","Any","October 2025","Fully Funded","Open to exceptional students from eligible countries demonstrating leadership.","https://www.rhodeshouse.ox.ac.uk/scholarships/"),
    _s("seed_017","Aga Khan Foundation International Scholarship","International","Various Universities","Master's","Any","March 2026","50% grant + 50% loan","Open to citizens of select developing countries with financial need and academic merit.","https://www.akdn.org/our-agencies/aga-khan-foundation/"),
    _s("seed_018","TWAS-CNPq Postgraduate Fellowship","Brazil","Brazilian Universities","PhD","STEM","August 2025","R$2,200/month","Open to scientists from developing countries for research in natural sciences.","https://twas.org/opportunity/twas-cnpq-postgraduate-fellowship-programme"),
    _s("seed_019","Eiffel Excellence Scholarship – France","France","French Grandes Écoles","Master's","STEM","January 2026","€1,181/month","Open to international students aged under 30 for master's programmes in France.","https://www.campusfrance.org/en/eiffel-scholarship-program-of-excellence"),
    _s("seed_020","World Bank Group Scholarships","International","Partner Universities Worldwide","Master's","Social Sciences","February 2026","Fully Funded","Open to citizens of World Bank member developing countries with development experience.","https://www.worldbank.org/en/programs/scholarships"),
]

# ── main ───────────────────────────────────────────────────────────────────

def run_scraper(use_seed: bool = False, max_pages: int = 3) -> int:
    if use_seed:
        log.info("Using seed data (%d entries).", len(SEED_SCHOLARSHIPS))
        scholarships = SEED_SCHOLARSHIPS
    else:
        log.info("Starting live scraping…")
        scholarships = []
        try:
            scholarships += scrape_scholars4dev(max_pages=max_pages)
        except Exception as exc:
            log.error("Scholars4Dev failed: %s", exc)
        try:
            scholarships += scrape_scholarshippositions(max_pages=max_pages)
        except Exception as exc:
            log.error("ScholarshipPositions failed: %s", exc)
        if not scholarships:
            log.warning("Live scraping returned 0 results — using seed data.")
            scholarships = SEED_SCHOLARSHIPS

    # deduplicate
    seen, unique = set(), []
    for s in scholarships:
        if s["title"] not in seen:
            seen.add(s["title"])
            unique.append(s)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(unique)

    log.info("Saved %d scholarships → %s", len(unique), OUTPUT_CSV)
    return len(unique)


if __name__ == "__main__":
    run_scraper(use_seed="--seed" in sys.argv)