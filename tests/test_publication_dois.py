"""
Integrity checks for publication DOIs in the supervisor seed data, and for how
publications without a DOI are rendered in professor dossiers.
Network verification (doi.org + OpenAlex) lives in scripts/verify_publication_dois.py.
"""

import json
import re
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import pytest

from src.supervisors.analyzer import DossierSynthesizer
from src.supervisors.models import Publication
from src.supervisors.profiler import DossierProfiler
from src.supervisors.storage import StorageManager

ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "src" / "supervisors" / "data"
LEGACY_HK_DIR = ROOT / "hk_supervisor_intel" / "data"
DOI_URL = re.compile(r"^https://doi\.org/10\.\d{4,9}/\S+$")


def _seed_publications():
    pubs = []
    for prof_file in sorted(SEED_DIR.glob("*/professors.json")):
        for prof in json.loads(prof_file.read_text()):
            pubs.extend(p for p in prof.get("publications", []) if isinstance(p, dict))
    for pub_file in sorted(SEED_DIR.glob("*/publications.json")) + [LEGACY_HK_DIR / "publications.json"]:
        pubs.extend(json.loads(pub_file.read_text()))
    return pubs


SEED_PUBLICATIONS = _seed_publications()


@pytest.mark.parametrize("pub", SEED_PUBLICATIONS, ids=lambda p: p["publication_id"])
def test_seed_doi_is_empty_or_well_formed(pub):
    doi_url = pub["doi_or_url"]
    assert doi_url == "" or DOI_URL.match(doi_url), doi_url
    # 10.5555 is ACM's unregistered internal prefix; such DOIs never resolve at doi.org.
    assert "/10.5555/" not in doi_url


def test_each_doi_identifies_a_single_title():
    titles_by_doi = defaultdict(set)
    for pub in SEED_PUBLICATIONS:
        if pub["doi_or_url"]:
            titles_by_doi[pub["doi_or_url"].lower()].add(pub["title"].strip().lower())
    reused = {doi: titles for doi, titles in titles_by_doi.items() if len(titles) > 1}
    assert not reused


def test_ieee_article_numbers_are_not_reused_across_journals():
    # IEEE DOI suffixes end in a globally unique article number, e.g. 10.1109/TMC.2023.3302410.
    journals_by_article = defaultdict(set)
    for pub in SEED_PUBLICATIONS:
        match = re.match(r"^https://doi\.org/10\.1109/([a-z0-9-]+)\.\d{4}\.(\d{7})$", pub["doi_or_url"], re.I)
        if match:
            journals_by_article[match.group(2)].add(match.group(1).lower())
    reused = {num: journals for num, journals in journals_by_article.items() if len(journals) > 1}
    assert not reused


@pytest.mark.parametrize("prof_file,pub_file", [
    (SEED_DIR / "hong_kong" / "professors.json", SEED_DIR / "hong_kong" / "publications.json"),
    (LEGACY_HK_DIR / "researchers.json", LEGACY_HK_DIR / "publications.json"),
])
def test_hong_kong_publication_references_resolve(prof_file, pub_file):
    known = {p["publication_id"] for p in json.loads(pub_file.read_text())}
    for prof in json.loads(prof_file.read_text()):
        missing = [p for p in prof.get("publications", []) if p not in known]
        assert not missing, f"{prof['name']}: {missing}"


def test_legacy_hong_kong_publications_match_country_seed():
    assert json.loads((LEGACY_HK_DIR / "publications.json").read_text()) == \
        json.loads((SEED_DIR / "hong_kong" / "publications.json").read_text())


class TestDossierRenderingWithoutDoi:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        storage = StorageManager()
        self.professor = storage.get_professors("uk")[0]
        self.university = storage.get_universities("uk")[0]
        self.synthesizer = DossierSynthesizer()
        self.profiler = DossierProfiler(output_base_dir=tmp_path / "reports")

    def _render(self, publications):
        researcher = replace(self.professor, publications=publications)
        dossier = self.synthesizer.synthesize(researcher=researcher, university=self.university)
        return dossier, self.profiler.render_professor_dossier_markdown(dossier)

    def test_missing_doi_is_not_replaced_by_profile_url(self):
        pub = Publication(
            publication_id="no_doi", title="A Paper Without a DOI", authors=[self.professor.name],
            year=2024, venue="Workshop", doi_or_url=""
        )
        dossier, md = self._render([pub])
        assert dossier.major_publications[0].doi_or_url == ""
        doi_lines = [line for line in md.splitlines() if line.startswith("* **DOI / Link:**")]
        assert doi_lines == ["* **DOI / Link:** Not available"]

    def test_no_publications_does_not_invent_one(self):
        dossier, md = self._render([])
        assert dossier.major_publications == []
        assert "_No verified publications on record._" in md
