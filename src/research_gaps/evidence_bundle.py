"""Evidence Bundle engine for assembling up to 40 works with verified links per research problem."""

import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone

from src.research_gaps.models import (
    EvidenceWork,
    EvidenceBundle,
    ExtractedPaperInfo,
    LinkStatus,
    _normalize_doi,
)
from src.research_gaps.link_verifier import LinkVerifier
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class EvidenceBundleBuilder:
    """Builds evidence bundles of up to 40 works per research problem."""

    def __init__(self, link_verifier: Optional[LinkVerifier] = None):
        self.verifier = link_verifier or LinkVerifier()

    def _normalize_title(self, title: str) -> str:
        if not title:
            return ""
        return re.sub(r'[^a-z0-9]', '', title.lower())

    def _determine_role(self, title: str, abstract: str, is_claim_source: bool) -> str:
        """Assign role based on provenance and textual content."""
        if is_claim_source:
            return "gap_evidence"

        text = (title + " " + abstract).lower()
        if any(w in text for w in ["survey", "review", "overview", "taxonomy", "foundations", "advances in"]):
            return "background"
        if any(w in text for w in ["framework", "algorithm", "architecture", "mechanism", "protocol", "model"]):
            return "method"
        if any(w in text for w in ["dataset", "benchmark", "evaluation", "metrics", "testbed", "empirical"]):
            return "evaluation"
        return "related_work"

    def build_evidence_bundle(
        self,
        problem_id: str,
        claims_source_papers: Optional[List[Any]] = None,
        unsolved_works: Optional[List[Any]] = None,
        corpus_papers: Optional[List[Any]] = None,
        extra_retrieved_works: Optional[List[Any]] = None,
        max_works: int = 40,
    ) -> EvidenceBundle:
        """Assembles up to 40 works with complete metadata and working links."""
        claims_source_papers = claims_source_papers or []
        unsolved_works = unsolved_works or []
        corpus_papers = corpus_papers or []
        extra_retrieved_works = extra_retrieved_works or []

        candidate_pool: List[Dict[str, Any]] = []

        # 1. Claims source papers
        for p in claims_source_papers:
            meta = p.to_dict() if hasattr(p, "to_dict") else dict(p)
            meta["_role"] = "gap_evidence"
            meta["_priority"] = 1
            candidate_pool.append(meta)

        # 2. Unsolved check matched works
        for p in unsolved_works:
            meta = p.to_dict() if hasattr(p, "to_dict") else dict(p)
            if "_role" not in meta:
                meta["_role"] = self._determine_role(meta.get("title", ""), meta.get("abstract", ""), False)
            meta["_priority"] = 2
            candidate_pool.append(meta)

        # 3. Corpus papers by relevance
        for p in corpus_papers:
            meta = p.to_dict() if hasattr(p, "to_dict") else dict(p)
            if "_role" not in meta:
                meta["_role"] = self._determine_role(meta.get("title", ""), meta.get("abstract", ""), False)
            meta["_priority"] = 3
            candidate_pool.append(meta)

        # 4. Extra retrieved works
        for p in extra_retrieved_works:
            meta = p.to_dict() if hasattr(p, "to_dict") else dict(p)
            if "_role" not in meta:
                meta["_role"] = self._determine_role(meta.get("title", ""), meta.get("abstract", ""), False)
            meta["_priority"] = 4
            candidate_pool.append(meta)

        # Deduplicate candidates
        deduped: Dict[str, Dict[str, Any]] = {}
        for item in candidate_pool:
            doi = _normalize_doi(item.get("doi"))
            openalex_id = item.get("openalex_id") or item.get("openalex_author_id")
            if openalex_id and not str(openalex_id).startswith("W"):
                openalex_id = None
            norm_title = self._normalize_title(item.get("title", ""))

            # Key choice
            dedup_key = f"doi:{doi}" if doi else (f"oa:{openalex_id}" if openalex_id else f"title:{norm_title}")
            if not norm_title and not doi and not openalex_id:
                continue

            if dedup_key not in deduped:
                deduped[dedup_key] = item
            else:
                existing = deduped[dedup_key]
                # Keep higher priority role or richer metadata
                if item.get("_priority", 5) < existing.get("_priority", 5):
                    deduped[dedup_key] = item

        # Sort deduplicated pool by priority, citation count, recency
        sorted_candidates = list(deduped.values())
        role_score_map = {"gap_evidence": 5, "method": 4, "evaluation": 3, "background": 2, "related_work": 1}
        sorted_candidates.sort(
            key=lambda x: (
                role_score_map.get(x.get("_role", "related_work"), 1),
                x.get("relevance_score", 0.0),
                x.get("citation_count", 0),
                x.get("year", 0),
            ),
            reverse=True,
        )

        # Link verification & EvidenceWork construction
        works: List[EvidenceWork] = []
        for item in sorted_candidates:
            if len(works) >= max_works:
                break

            link_res = self.verifier.select_best_link(item)

            doi = _normalize_doi(item.get("doi"))
            authors = item.get("authors") or []
            if isinstance(authors, str):
                authors = [a.strip() for a in authors.split(",")]

            year = item.get("year") or 0
            if not year and item.get("publication_date"):
                match = re.search(r'(19|20)\d{2}', str(item.get("publication_date")))
                if match:
                    year = int(match.group(0))

            openalex_id = item.get("openalex_id")
            if openalex_id and not str(openalex_id).startswith("W"):
                openalex_id = None

            pid = item.get("paper_id") or item.get("id") or ""
            if not pid or "doi_" in pid or "paper_" in pid:
                if doi:
                    pid = f"doi:{doi}"
                elif openalex_id:
                    pid = f"openalex:{openalex_id}"
                else:
                    pid = f"work_{hashlib.md5(self._normalize_title(item.get('title', '')).encode()).hexdigest()[:12]}"

            work = EvidenceWork(
                ref_key="",  # Assigned in next pass
                paper_id=pid,
                doi=doi,
                openalex_id=openalex_id,
                title=item.get("title") or "Untitled",
                authors=authors,
                year=year,
                venue=item.get("venue") or "",
                link_url=link_res.link_url,
                link_type=link_res.link_type,
                link_status=link_res.link_status,
                verified_at=link_res.verified_at,
                role=item.get("_role", "related_work"),
                citation_count=item.get("citation_count") or 0,
                relevance_score=float(item.get("relevance_score") or 0.0),
            )
            works.append(work)

        # Assign stable keys R1, R2, ... R_N
        for idx, w in enumerate(works):
            w.ref_key = f"R{idx + 1}"

        bundle = EvidenceBundle(problem_id=problem_id, works=works)
        return bundle


def load_evidence_bundles(bundles_file: Optional[Path] = None) -> Dict[str, EvidenceBundle]:
    """Load persisted evidence bundles from data/evidence_bundles.json."""
    filepath = bundles_file or (DATA_DIR / "evidence_bundles.json")
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: EvidenceBundle.from_dict(v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"Failed to load evidence bundles: {e}")
        return {}


def save_evidence_bundles(bundles: Dict[str, EvidenceBundle], bundles_file: Optional[Path] = None) -> None:
    """Atomically persist evidence bundles to disk."""
    filepath = bundles_file or (DATA_DIR / "evidence_bundles.json")
    try:
        data = {k: v.to_dict() for k, v in bundles.items()}
        _atomic_write_json(filepath, data)
    except Exception as e:
        logger.error(f"Failed to save evidence bundles: {e}")
