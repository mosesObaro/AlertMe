"""
Verify every publication DOI in the supervisor seed data against doi.org and OpenAlex.

For each publication with a DOI, checks that:
1. the DOI is registered (doi.org handle API returns responseCode 1),
2. OpenAlex has a work for the DOI whose title matches the stored title, and
3. the professor the publication is attached to appears among that work's authors.

Exits non-zero if any check fails. Usage: python scripts/verify_publication_dois.py
"""

import difflib
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIRS = [ROOT / "src" / "supervisors" / "data"]
LEGACY_HK = ROOT / "hk_supervisor_intel" / "data"
DOI_PREFIX = "https://doi.org/"
TITLE_THRESHOLD = 0.9


def norm(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def name_parts(full_name):
    name = re.sub(r"\(.*?\)", "", full_name)
    name = re.sub(r"^(Prof\.|Dr\.)\s*", "", name.strip())
    name = re.sub(r",?\s*Jr\.?$", "", name.strip())
    tokens = name.replace(".", ". ").split()
    return tokens[0], tokens[-1]


def name_matches(display_name, given, family):
    tokens = norm(display_name).split()
    fam = norm(family)
    if fam not in tokens:
        return False
    others = [t for t in tokens if t != fam]
    g = norm(given).replace(" ", "")
    return g in others or "".join(others).startswith(g)


def collect_publications():
    """Yields (source_file, professor_name, publication_dict) for every seed publication."""
    for data_dir in DATA_DIRS:
        for prof_file in sorted(data_dir.glob("*/professors.json")):
            standalone = {}
            pub_file = prof_file.parent / "publications.json"
            if pub_file.exists():
                standalone = {p["publication_id"]: p for p in json.loads(pub_file.read_text())}
            for prof in json.loads(prof_file.read_text()):
                for pub in prof.get("publications", []):
                    record = standalone.get(pub) if isinstance(pub, str) else pub
                    if record:
                        yield prof_file, prof["name"], record

    legacy_pubs = {p["publication_id"]: p for p in json.loads((LEGACY_HK / "publications.json").read_text())}
    for prof in json.loads((LEGACY_HK / "researchers.json").read_text()):
        for pub_id in prof.get("publications", []):
            if pub_id in legacy_pubs:
                yield LEGACY_HK / "researchers.json", prof["name"], legacy_pubs[pub_id]


def get_json(session, url):
    for attempt in range(4):
        resp = session.get(url, timeout=30)
        if resp.status_code == 429 or resp.status_code >= 500:
            time.sleep(2 * (attempt + 1))
            continue
        return resp.status_code, (resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {})
    return resp.status_code, {}


def verify(session, prof_name, pub):
    url = pub.get("doi_or_url", "")
    if not url:
        return []
    if not url.startswith(DOI_PREFIX):
        return [f"not a doi.org URL: {url}"]
    doi = url[len(DOI_PREFIX):]
    problems = []

    _, handle = get_json(session, f"https://doi.org/api/handles/{quote(doi, safe='/')}")
    if handle.get("responseCode") != 1:
        problems.append(f"DOI not registered at doi.org (responseCode={handle.get('responseCode')})")

    status, work = get_json(session, f"https://api.openalex.org/works/doi:{quote(doi, safe='/')}?select=title,authorships")
    if status != 200:
        problems.append(f"DOI not found in OpenAlex (HTTP {status})")
        return problems

    similarity = difflib.SequenceMatcher(None, norm(pub["title"]), norm(work.get("title"))).ratio()
    # OpenAlex sometimes drops the subtitle that Crossref records separately, e.g. "DIPA2" for "DIPA2: An Image ...".
    if similarity < TITLE_THRESHOLD and not norm(pub["title"]).startswith(norm(work.get("title"))):
        problems.append(f"title mismatch ({similarity:.2f}): OpenAlex has '{work.get('title')}'")

    given, family = name_parts(prof_name)
    names = [a.get("raw_author_name") or (a.get("author") or {}).get("display_name", "") for a in work.get("authorships", [])]
    if not any(name_matches(n, given, family) for n in names):
        problems.append(f"{prof_name} not among OpenAlex authors")
    return problems


def main():
    session = requests.Session()
    session.headers["User-Agent"] = "AlertMe-doi-verifier/1.0"
    checked, failures = 0, 0
    for source, prof_name, pub in collect_publications():
        problems = verify(session, prof_name, pub)
        if pub.get("doi_or_url"):
            checked += 1
        if problems:
            failures += 1
            print(f"FAIL {source.relative_to(ROOT)} | {prof_name} | {pub['publication_id']} | {pub.get('doi_or_url')}")
            for problem in problems:
                print(f"     - {problem}")
    print(f"\nChecked {checked} DOIs: {checked - failures} verified, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
