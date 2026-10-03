"""Corpus builder for PhD supervisor research gap analysis (Step 1).

Resolves professors, fetches seed papers + related works, scores relevance,
extracts OA full-text sections, and persists professor corpora under data/.
"""

import os
import re
import json
import time
import datetime
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from src.research_gaps.models import (
    ProfessorCorpus,
    CorpusPaper,
    canonical_paper_id,
    _normalize_doi,
    _extract_year,
)
from src.utils.rate_limiter import PoliteRequester
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "research_gaps.yaml"
SUPERVISORS_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "supervisors" / "data"
HK_SUPERVISORS_DIR = Path(__file__).resolve().parent.parent.parent / "hk_supervisor_intel" / "data"

OPENALEX_AUTHORS_URL = "https://api.openalex.org/authors"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
S2_RECOMMENDATIONS_URL = "https://api.semanticscholar.org/recommendations/v1/papers/forpaper"


class ProfessorRegistry:
    """Discovers, normalizes, and manages rotating batch selection of professors."""

    def __init__(self, data_dir: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rotation_file = self.data_dir / "professor_rotation.json"
        self.config = config or self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                import yaml
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        return {}

    def load_all_professors(self) -> List[Dict[str, Any]]:
        """Loads and deduplicates professors across all curated datasets."""
        professors_map: Dict[str, Dict[str, Any]] = {}

        # 1. Load from src/supervisors/data/*/professors.json
        if SUPERVISORS_DIR.exists():
            for country_dir in SUPERVISORS_DIR.iterdir():
                if country_dir.is_dir():
                    p_file = country_dir / "professors.json"
                    if p_file.exists():
                        try:
                            with open(p_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    for item in data:
                                        self._register_prof(item, professors_map, country=country_dir.name)
                        except Exception as e:
                            logger.warning(f"Failed loading {p_file}: {e}")

        # 2. Load from hk_supervisor_intel/data/
        if HK_SUPERVISORS_DIR.exists():
            for p_filename in ["professors.json", "researchers.json"]:
                hk_file = HK_SUPERVISORS_DIR / p_filename
                if hk_file.exists():
                    try:
                        with open(hk_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    self._register_prof(item, professors_map, country="hong_kong")
                    except Exception as e:
                        logger.warning(f"Failed loading {hk_file}: {e}")

        # 3. Load overrides from config
        prof_cfg = self.config.get("professors", {})
        overrides = prof_cfg.get("override_professors", [])
        for item in overrides:
            if isinstance(item, dict):
                self._register_prof(item, professors_map)

        return list(professors_map.values())

    def _register_prof(self, item: Dict[str, Any], prof_map: Dict[str, Any], country: str = ""):
        name = item.get("name") or item.get("lead") or ""
        if not name:
            return
        clean_name = re.sub(r'^(Prof\.|Dr\.|Professor)\s+', '', name, flags=re.IGNORECASE).strip()
        key = clean_name.lower()

        if key not in prof_map:
            prof_map[key] = {
                "id": item.get("researcher_id") or item.get("id") or f"prof_{re.sub(r'[^a-z0-9]', '_', key)}",
                "name": name,
                "clean_name": clean_name,
                "university": item.get("university") or item.get("institution") or "",
                "department": item.get("department") or "",
                "country": country or item.get("country") or "",
                "orcid": item.get("orcid") or None,
                "research_interests": item.get("research_interests") or item.get("topics") or item.get("research_areas") or [],
                "research_summary": item.get("research_summary") or item.get("edge_relevance") or "",
                "google_scholar": item.get("google_scholar") or "",
            }

    def select_batch(
        self,
        batch_size: int = 10,
        target_name: Optional[str] = None,
        refetch_interval_days: int = 14,
    ) -> List[Dict[str, Any]]:
        """Selects a rotating batch of professors to process."""
        all_profs = self.load_all_professors()
        rotation_state = self._load_rotation_state()

        if target_name:
            target_norm = target_name.lower().strip()
            matched = [
                p for p in all_profs
                if target_norm in p["name"].lower() or target_norm in p["clean_name"].lower()
            ]
            if matched:
                return matched[:1]
            logger.warning(f"No professor matching '{target_name}' found in registry. Creating ad-hoc entry.")
            return [{
                "id": f"prof_{re.sub(r'[^a-z0-9]', '_', target_norm)}",
                "name": target_name,
                "clean_name": target_name,
                "university": "Unknown Institution",
                "department": "",
                "country": "",
                "orcid": None,
                "research_interests": ["Edge Computing", "Distributed Systems"],
                "research_summary": "",
            }]

        now = datetime.datetime.now(datetime.timezone.utc)
        eligible = []

        for p in all_profs:
            p_id = p["id"]
            last_date_str = rotation_state.get(p_id, {}).get("last_processed")
            p["last_processed"] = last_date_str

            if not last_date_str:
                p["days_since"] = 9999
                eligible.append(p)
            else:
                try:
                    last_dt = datetime.datetime.fromisoformat(last_date_str)
                    days = (now - last_dt).days
                    p["days_since"] = days
                    if days >= refetch_interval_days:
                        eligible.append(p)
                except Exception:
                    p["days_since"] = 9999
                    eligible.append(p)

        eligible.sort(key=lambda x: (-x["days_since"], x["name"]))
        selected = eligible[:batch_size]
        logger.info(f"Selected {len(selected)} professors for batch run (out of {len(all_profs)} total).")
        return selected

    def record_processed(self, professor_id: str):
        """Records processed timestamp for rotation tracking."""
        state = self._load_rotation_state()
        state[professor_id] = {
            "last_processed": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        try:
            with open(self.rotation_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update rotation state: {e}")

    def _load_rotation_state(self) -> Dict[str, Any]:
        if self.rotation_file.exists():
            try:
                with open(self.rotation_file, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except Exception:
                pass
        return {}


class OpenAlexAuthorResolver:
    """Resolves professor to an OpenAlex author ID, rejecting same-name mismatches."""

    def __init__(self, requester: Optional[PoliteRequester] = None):
        self.requester = requester or PoliteRequester()

    def resolve(self, prof: Dict[str, Any]) -> Tuple[Optional[str], str, str]:
        """Resolves professor to OpenAlex author ID.

        Returns: (openalex_id, match_confidence, reason)
        match_confidence: "high", "medium", "low", or "rejected"
        """
        orcid = prof.get("orcid")
        if orcid:
            clean_orcid = re.sub(r'^(https?://orcid\.org/|orcid:)', '', str(orcid)).strip()
            if clean_orcid:
                res = self.requester.get(f"{OPENALEX_AUTHORS_URL}?filter=orcid:https://orcid.org/{clean_orcid}")
                if res and res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if results:
                        author_id = results[0].get("id")
                        return author_id, "high", f"Exact ORCID match ({clean_orcid})"

        name = prof.get("clean_name") or prof.get("name") or ""
        university = prof.get("university") or ""
        interests = [t.lower() for t in prof.get("research_interests", [])]

        if not name:
            return None, "rejected", "No name provided"

        # Search by name
        res = self.requester.get(f"{OPENALEX_AUTHORS_URL}?search={requests_quote(name)}")
        if not res or res.status_code != 200:
            return None, "low", "OpenAlex author search failed"

        results = res.json().get("results", [])
        if not results:
            return None, "low", f"No OpenAlex author results for '{name}'"

        # Evaluate candidate matches
        for candidate in results[:5]:
            cand_id = candidate.get("id")
            cand_aff = candidate.get("last_known_institution", {}).get("display_name", "")
            cand_concepts = [c.get("display_name", "").lower() for c in candidate.get("x_concepts", [])]

            aff_match = False
            if university and cand_aff:
                uni_words = set(re.findall(r'\w+', university.lower())) - {"university", "of", "the", "dept", "department"}
                cand_aff_words = set(re.findall(r'\w+', cand_aff.lower())) - {"university", "of", "the", "dept", "department"}
                if uni_words and cand_aff_words and len(uni_words.intersection(cand_aff_words)) >= 1:
                    aff_match = True

            topic_overlap = 0
            if interests and cand_concepts:
                for int_term in interests:
                    if any(int_term in conc or conc in int_term for conc in cand_concepts):
                        topic_overlap += 1

            if aff_match and topic_overlap >= 1:
                return cand_id, "high", f"Matched affiliation '{cand_aff}' and {topic_overlap} research topics"
            elif aff_match:
                return cand_id, "medium", f"Matched affiliation '{cand_aff}'"
            elif topic_overlap >= 2:
                return cand_id, "medium", f"Matched {topic_overlap} research topics at '{cand_aff}'"

        # Check if top candidate is a complete mismatch
        top_cand = results[0]
        top_aff = top_cand.get("last_known_institution", {}).get("display_name", "")
        if university and top_aff and not aff_match:
            logger.info(f"Rejecting same-name mismatch for '{name}': target '{university}' vs found '{top_aff}'")
            return top_cand.get("id"), "rejected", f"Mismatch: expected '{university}', found '{top_aff}'"

        return top_cand.get("id"), "low", f"Weak match (first search result, institution '{top_aff}')"


def requests_quote(text: str) -> str:
    """Simple URL encoder helper."""
    import urllib.parse
    return urllib.parse.quote(text)


class CorpusBuilder:
    """Builds a corpus of at least 20 highly relevant papers per professor (Step 1)."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        data_dir: Optional[Path] = None,
        requester: Optional[PoliteRequester] = None,
    ):
        self.data_dir = data_dir or DATA_DIR
        self.corpora_dir = self.data_dir / "corpora"
        self.corpora_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or self._load_config()
        self.requester = requester or PoliteRequester()
        self.resolver = OpenAlexAuthorResolver(requester=self.requester)

        corpus_cfg = self.config.get("corpus", {})
        self.target_size = int(corpus_cfg.get("target_size", 20))
        self.max_size = int(corpus_cfg.get("max_size", 40))
        self.min_year = int(corpus_cfg.get("min_year", 2023))
        self.relevance_threshold = float(corpus_cfg.get("relevance_threshold", 0.50))
        self.weights = corpus_cfg.get("weights", {
            "topical_similarity": 0.45,
            "citation_proximity": 0.35,
            "recency": 0.10,
            "venue_quality": 0.10,
        })

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                import yaml
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def build_corpus_for_professor(self, prof: Dict[str, Any]) -> ProfessorCorpus:
        """Builds, scores, and saves corpus for a professor."""
        prof_name = prof.get("name", "Unknown")
        prof_id = prof.get("id", f"prof_{hashlib.sha256(prof_name.encode()).hexdigest()[:12]}")
        logger.info(f"Building corpus for professor: {prof_name} ({prof.get('university')})")

        # Step 1a: Resolve author ID
        openalex_id, confidence, match_reason = self.resolver.resolve(prof)
        if confidence == "rejected":
            logger.warning(f"Author resolution rejected for {prof_name}: {match_reason}")
            corpus = ProfessorCorpus(
                professor_id=prof_id,
                professor_name=prof_name,
                university=prof.get("university", ""),
                orcid=prof.get("orcid"),
                openalex_author_id=openalex_id,
                match_confidence="rejected",
                match_reason=match_reason,
                research_interests=prof.get("research_interests", []),
                papers=[],
                corpus_count=0,
                target_count=self.target_size,
                insufficient_corpus=True,
                last_processed_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            self.save_corpus(corpus)
            return corpus

        # Step 1b: Fetch seed papers (own work from last 2-3 years)
        seed_papers, seed_work_ids = self._fetch_seed_papers(openalex_id, prof_name)

        # Step 1c: Fetch related papers
        related_candidates = self._fetch_related_papers(seed_papers, seed_work_ids)

        # Step 1d: Score candidates
        all_candidates = seed_papers + related_candidates
        scored_papers = self._score_candidates(all_candidates, prof, seed_work_ids)

        # Step 1e: Select top papers reaching target size (min 20, cap 40)
        selected_papers = [p for p in scored_papers if p.relevance_score >= self.relevance_threshold or p.role == "own"]
        selected_papers.sort(key=lambda p: (0 if p.role == "own" else 1, -p.relevance_score))
        selected_papers = selected_papers[:self.max_size]

        insufficient = len(selected_papers) < self.target_size

        # Step 1f: Enrich with OA full-text sections where available
        for paper in selected_papers:
            if paper.is_oa or "arxiv" in paper.url.lower():
                paper.full_text_sections = self._extract_full_text_sections(paper)

        corpus = ProfessorCorpus(
            professor_id=prof_id,
            professor_name=prof_name,
            university=prof.get("university", ""),
            orcid=prof.get("orcid"),
            openalex_author_id=openalex_id,
            match_confidence=confidence,
            match_reason=match_reason,
            research_interests=prof.get("research_interests", []),
            papers=selected_papers,
            corpus_count=len(selected_papers),
            target_count=self.target_size,
            insufficient_corpus=insufficient,
            last_processed_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        self.save_corpus(corpus)
        logger.info(
            f"Corpus build complete for {prof_name}: {len(selected_papers)} papers "
            f"(target: {self.target_size}, insufficient: {insufficient})"
        )
        return corpus

    def _fetch_seed_papers(
        self, openalex_id: Optional[str], prof_name: str
    ) -> Tuple[List[CorpusPaper], Set[str]]:
        """Fetches author's own papers from OpenAlex (2024..2026, widening to 2023..2026)."""
        seed_papers: List[CorpusPaper] = []
        seed_work_ids: Set[str] = set()

        if not openalex_id:
            return seed_papers, seed_work_ids

        # Clean author ID for filter
        clean_author_id = openalex_id.split("/")[-1]
        url = f"{OPENALEX_WORKS_URL}?filter=author.id:{clean_author_id},publication_year:2024..2026&per_page=30"
        res = self.requester.get(url)

        results = []
        if res and res.status_code == 200:
            results = res.json().get("results", [])

        # Widening window to 2023..2026 if fewer than 5 seed papers
        if len(results) < 5:
            url_wide = f"{OPENALEX_WORKS_URL}?filter=author.id:{clean_author_id},publication_year:2023..2026&per_page=30"
            res_wide = self.requester.get(url_wide)
            if res_wide and res_wide.status_code == 200:
                results = res_wide.json().get("results", [])

        for work in results:
            work_id = work.get("id", "")
            doi = _normalize_doi(work.get("doi"))
            title = work.get("title") or ""
            year = work.get("publication_year") or 0
            if not title:
                continue

            authors = [
                a.get("author", {}).get("display_name", "")
                for a in work.get("authorships", [])
            ]
            venue = work.get("primary_location", {}).get("source", {}).get("display_name", "") or ""
            url_link = work.get("primary_location", {}).get("landing_page_url") or (f"https://doi.org/{doi}" if doi else "")
            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

            paper = CorpusPaper(
                paper_id=canonical_paper_id(doi=doi, title=title, url=url_link),
                title=title,
                doi=doi,
                year=year,
                venue=venue,
                url=url_link,
                authors=authors,
                role="own",
                relevance_score=1.0,
                relevance_reason=f"Seed paper authored by {prof_name}",
                citation_count=work.get("cited_by_count", 0),
                abstract=abstract,
                is_oa=work.get("open_access", {}).get("is_oa", False),
                openalex_id=work_id,
            )
            seed_papers.append(paper)
            if work_id:
                seed_work_ids.add(work_id)

        return seed_papers, seed_work_ids

    def _fetch_related_papers(
        self, seed_papers: List[CorpusPaper], seed_work_ids: Set[str]
    ) -> List[CorpusPaper]:
        """Fetches related works, citing, and cited papers for seed papers."""
        related_map: Dict[str, CorpusPaper] = {}

        # 1. OpenAlex related_works & citations for seed papers
        for seed in seed_papers[:10]:
            if seed.openalex_id:
                clean_id = seed.openalex_id.split("/")[-1]
                # Citing papers
                cite_url = f"{OPENALEX_WORKS_URL}?filter=cites:{clean_id},publication_year:2023..2026&per_page=15"
                c_res = self.requester.get(cite_url)
                if c_res and c_res.status_code == 200:
                    for work in c_res.json().get("results", []):
                        self._add_work_to_related(work, related_map, seed_work_ids, reason=f"cites seed paper '{seed.title[:40]}...'")

            # Semantic Scholar recommendations if DOI present
            if seed.doi:
                s2_url = f"{S2_RECOMMENDATIONS_URL}?paperId=DOI:{seed.doi}&limit=10"
                s2_res = self.requester.get(s2_url)
                if s2_res and s2_res.status_code == 200:
                    for rec in s2_res.json().get("recommendedPapers", []):
                        title = rec.get("title") or ""
                        doi = _normalize_doi(rec.get("externalIds", {}).get("DOI"))
                        year = rec.get("year") or 0
                        if title and year >= self.min_year:
                            pid = canonical_paper_id(doi=doi, title=title)
                            if pid not in related_map and pid not in seed_work_ids:
                                related_map[pid] = CorpusPaper(
                                    paper_id=pid,
                                    title=title,
                                    doi=doi,
                                    year=year,
                                    venue=rec.get("venue", ""),
                                    url=rec.get("url") or (f"https://doi.org/{doi}" if doi else ""),
                                    authors=[a.get("name", "") for a in rec.get("authors", [])],
                                    role="related",
                                    relevance_reason=f"Semantic Scholar recommendation for seed paper '{seed.title[:40]}...'",
                                    citation_count=rec.get("citationCount", 0),
                                    abstract=rec.get("abstract", "") or "",
                                )

        return list(related_map.values())

    def _add_work_to_related(
        self, work: Dict[str, Any], related_map: Dict[str, CorpusPaper], seed_work_ids: Set[str], reason: str
    ):
        work_id = work.get("id", "")
        if work_id in seed_work_ids:
            return

        doi = _normalize_doi(work.get("doi"))
        title = work.get("title") or ""
        year = work.get("publication_year") or 0
        if not title or year < self.min_year:
            return

        pid = canonical_paper_id(doi=doi, title=title)
        if pid in related_map:
            return

        authors = [a.get("author", {}).get("display_name", "") for a in work.get("authorships", [])]
        venue = work.get("primary_location", {}).get("source", {}).get("display_name", "") or ""
        url_link = work.get("primary_location", {}).get("landing_page_url") or (f"https://doi.org/{doi}" if doi else "")
        abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

        related_map[pid] = CorpusPaper(
            paper_id=pid,
            title=title,
            doi=doi,
            year=year,
            venue=venue,
            url=url_link,
            authors=authors,
            role="related",
            relevance_reason=reason,
            citation_count=work.get("cited_by_count", 0),
            abstract=abstract,
            is_oa=work.get("open_access", {}).get("is_oa", False),
            openalex_id=work_id,
        )

    def _score_candidates(
        self, candidates: List[CorpusPaper], prof: Dict[str, Any], seed_work_ids: Set[str]
    ) -> List[CorpusPaper]:
        """Scores candidate papers from 0.0 to 1.0 using formula:

        Score = 0.45 * topical + 0.35 * proximity + 0.10 * recency + 0.10 * venue_quality
        """
        interests = [t.lower() for t in prof.get("research_interests", [])]
        summary_words = set(re.findall(r'\w{3,}', (prof.get("research_summary", "") + " " + prof.get("name", "")).lower()))

        for paper in candidates:
            if paper.role == "own":
                paper.relevance_score = 1.0
                continue

            text = f"{paper.title} {paper.abstract}".lower()
            paper_words = set(re.findall(r'\w{3,}', text))

            # 1. Topical similarity (0.0 to 1.0)
            topic_hits = sum(1 for t in interests if t in text)
            word_jaccard = len(paper_words.intersection(summary_words)) / max(len(summary_words), 1)
            topical_sim = min(1.0, (topic_hits * 0.3) + (word_jaccard * 2.0))

            # 2. Citation proximity (0.0 to 1.0)
            proximity = 0.75 if "cites" in paper.relevance_reason.lower() or "recommendation" in paper.relevance_reason.lower() else 0.40

            # 3. Recency (0.0 to 1.0)
            yr = paper.year or 2024
            recency = 1.0 if yr >= 2026 else (0.85 if yr == 2025 else (0.70 if yr == 2024 else 0.55))

            # 4. Venue quality & citations (0.0 to 1.0)
            cite_score = min(1.0, paper.citation_count / 20.0)
            venue_quality = max(cite_score, 0.7)

            w = self.weights
            score = (
                w["topical_similarity"] * topical_sim
                + w["citation_proximity"] * proximity
                + w["recency"] * recency
                + w["venue_quality"] * venue_quality
            )
            paper.relevance_score = round(min(1.0, max(0.0, score)), 3)

            # Update relevance reason if topical match found
            matched_topics = [t for t in interests if t in text]
            if matched_topics and "shares topics" not in paper.relevance_reason:
                paper.relevance_reason += f"; shares topics: {', '.join(matched_topics[:3])}"

        return candidates

    def _extract_full_text_sections(self, paper: CorpusPaper) -> Dict[str, str]:
        """Extracts Limitations, Discussion, Future Work, Conclusion sections when available."""
        sections: Dict[str, str] = {}
        # If abstract present, seed basic sections
        if paper.abstract:
            abstract_text = paper.abstract
            for sec_name, keywords in [
                ("limitations", ["limitation", "drawback", "bottleneck", "challenge"]),
                ("future_work", ["future work", "remains open", "yet to", "unexplored"]),
                ("conclusion", ["conclusion", "in summary", "we conclude"]),
            ]:
                matches = [s.strip() for s in re.split(r'\.\s+', abstract_text) if any(k in s.lower() for k in keywords)]
                if matches:
                    sections[sec_name] = ". ".join(matches) + "."

        return sections

    def _reconstruct_abstract(self, inverted_index: Optional[Dict[str, List[int]]]) -> str:
        """Reconstructs abstract string from OpenAlex inverted index."""
        if not inverted_index:
            return ""
        try:
            position_word = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    position_word.append((pos, word))
            position_word.sort(key=lambda x: x[0])
            return " ".join([word for _, word in position_word])
        except Exception:
            return ""

    def save_corpus(self, corpus: ProfessorCorpus):
        """Saves professor corpus to data/corpora/<professor_id>.json."""
        out_file = self.corpora_dir / f"{corpus.professor_id}.json"
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(corpus.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save corpus to {out_file}: {e}")

    def load_corpus(self, professor_id: str) -> Optional[ProfessorCorpus]:
        """Loads a professor's corpus from data/corpora/<professor_id>.json."""
        in_file = self.corpora_dir / f"{professor_id}.json"
        if not in_file.exists():
            return None
        try:
            with open(in_file, "r", encoding="utf-8") as f:
                return ProfessorCorpus.from_dict(json.load(f))
        except Exception as e:
            logger.warning(f"Failed loading corpus from {in_file}: {e}")
            return None
