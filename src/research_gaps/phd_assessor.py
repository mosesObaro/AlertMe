"""PhD qualification assessor implementing Dublin Descriptors (Level 8) & EQF 8 rubric.

Evaluates unsolved problem clusters across 6 dimensions:
1. Original: open/partial status, few direct solutions.
2. Significant: support count, distinct professors, citation levels, yearly growth.
3. Doctoral Scope: at least 2 distinct sub-problems for 2-4 research questions.
4. Rigorous: measurable metrics, benchmarks, datasets or testbeds.
5. Feasible: open code/datasets referenced, no proprietary-only signal.
6. Publishable: related work appears in refereed venues.
"""

import re
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from src.research_gaps.models import (
    UnsolvedProblemCluster,
    CorpusPaper,
    ProfessorCorpus,
    PhDQualificationCriterion,
    PhDQualificationResult,
    FeasibilityAssessment,
    EvidenceClaim,
)
from src.research_gaps.feasibility import FeasibilityAssessor
from src.utils.logger import logger

REFEREED_VENUES_KEYWORDS = [
    "ieee", "acm", "usenix", "springer", "elsevier", "neurips", "icml", "iclr",
    "kdd", "infocom", "mobicom", "sigcomm", "nsdi", "osdi", "sec", "iot",
    "tosem", "tse", "tmc", "tpds", "tkde", "tvt", "sensys", "mobisys",
    "asplos", "micro", "isca", "eurosys", "vldb", "sigmod", "conference", "journal", "transactions"
]

METRICS_BENCHMARKS_KEYWORDS = [
    "dataset", "benchmark", "accuracy", "latency", "throughput", "energy",
    "overhead", "memory", "imagenet", "cifar", "kitti", "testbed", "baseline",
    "evaluation", "metric", "precision", "recall", "f1", "execution time"
]

OPEN_ARTIFACTS_KEYWORDS = [
    "github.com", "gitlab", "huggingface", "open source", "public dataset",
    "available at", "repository", "source code", "open-source", "zenodo", "kaggle"
]

PROPRIETARY_KEYWORDS = [
    "proprietary dataset", "internal dataset", "commercial nda", "trade secret",
    "not publicly available", "closed source", "private dataset"
]


class PhDQualificationAssessor(FeasibilityAssessor):
    """Assesses whether an unsolved research problem qualifies for a PhD thesis."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        cache_dir: Optional[Path] = None,
    ):
        super().__init__(config=config, cache_dir=cache_dir)
        refereed_cfg = self.config.get("phd_qualification", {}).get("refereed_venues", [])
        self.refereed_venues = set(v.lower() for v in (refereed_cfg or REFEREED_VENUES_KEYWORDS))

    def evaluate_original(self, cluster: UnsolvedProblemCluster) -> PhDQualificationCriterion:
        """(1) Original: open or partial status, few direct solutions."""
        sol_status = cluster.solution_status.lower()
        sol_count = len(cluster.solution_evidence or [])

        if sol_status == "open" and sol_count == 0:
            verdict = "pass"
            rule_desc = "Problem is open with 0 identified direct solutions in recent literature."
        elif sol_status in ("open", "partially_addressed") or sol_count <= 3:
            verdict = "partial"
            rule_desc = f"Problem is {sol_status} with {sol_count} partial/mitigating works identified."
        else:
            verdict = "fail"
            rule_desc = f"Problem is addressed with {sol_count} direct solution works."

        confidence = "high" if len(cluster.quoted_claims) >= 2 else "medium"
        return PhDQualificationCriterion(
            criterion_name="original",
            verdict=verdict,
            numbers={"solution_status": sol_status, "solution_count": sol_count},
            rule_description=rule_desc,
            confidence=confidence,
        )

    def evaluate_significant(
        self,
        cluster: UnsolvedProblemCluster,
        matching_papers: List[CorpusPaper],
    ) -> PhDQualificationCriterion:
        """(2) Significant: support_count, distinct professors, citations, yearly growth."""
        support_count = cluster.support_count or len(cluster.quoted_claims)
        distinct_profs = len(set(cluster.professors or []))
        total_citations = sum(p.citation_count for p in matching_papers)
        recent_papers = sum(1 for p in matching_papers if p.year >= 2024)
        recent_ratio = round(recent_papers / max(1, len(matching_papers)), 2)

        if support_count >= 3 and (distinct_profs >= 2 or total_citations >= 15 or recent_ratio >= 0.4):
            verdict = "pass"
            rule_desc = (
                f"High research significance: supported by {support_count} claims across {distinct_profs} "
                f"professors with {total_citations} total citations and {recent_ratio * 100:.0f}% recent work."
            )
        elif support_count >= 1:
            verdict = "partial"
            rule_desc = (
                f"Moderate significance: supported by {support_count} claim(s), {distinct_profs} professor(s), "
                f"and {total_citations} citations."
            )
        else:
            verdict = "fail"
            rule_desc = "Insufficient claim volume or community interest."

        confidence = "high" if total_citations >= 10 or support_count >= 3 else "medium"
        return PhDQualificationCriterion(
            criterion_name="significant",
            verdict=verdict,
            numbers={
                "support_count": support_count,
                "distinct_professors": distinct_profs,
                "total_citations": total_citations,
                "recent_ratio": recent_ratio,
            },
            rule_description=rule_desc,
            confidence=confidence,
        )

    def evaluate_doctoral_scope(self, cluster: UnsolvedProblemCluster) -> PhDQualificationCriterion:
        """(3) Doctoral Scope: at least 2 distinct sub-problems for 2-4 research questions."""
        claims = cluster.quoted_claims or []
        distinct_claims = list(set(c.claim_text for c in claims))
        claim_count = len(distinct_claims)
        estimated_rqs = max(2, min(4, claim_count + 1 if claim_count > 0 else 0))

        if claim_count >= 2:
            verdict = "pass"
            rule_desc = f"Broad doctoral scope: {claim_count} distinct sub-problems support {estimated_rqs} research questions."
        elif claim_count == 1:
            verdict = "partial"
            rule_desc = f"Focused scope: 1 sub-problem identified, supporting {estimated_rqs} research questions."
        else:
            verdict = "fail"
            rule_desc = "Narrow or undefined scope with zero distinct claims."

        confidence = "high" if claim_count >= 2 else "medium"
        return PhDQualificationCriterion(
            criterion_name="doctoral_scope",
            verdict=verdict,
            numbers={
                "distinct_sub_problems": claim_count,
                "estimated_research_questions": estimated_rqs,
            },
            rule_description=rule_desc,
            confidence=confidence,
        )

    def evaluate_rigorous(
        self,
        cluster: UnsolvedProblemCluster,
        matching_papers: List[CorpusPaper],
    ) -> PhDQualificationCriterion:
        """(4) Rigorous: measurable metrics, benchmarks, datasets or testbeds."""
        found_terms: Set[str] = set()
        combined_text = " ".join([c.claim_text for c in cluster.quoted_claims]).lower()

        for paper in matching_papers:
            combined_text += " " + (paper.title or "").lower()
            combined_text += " " + (paper.abstract or "").lower()
            for sec_text in paper.full_text_sections.values():
                combined_text += " " + sec_text.lower()

        for term in METRICS_BENCHMARKS_KEYWORDS:
            if re.search(rf"\b{re.escape(term)}\b", combined_text):
                found_terms.add(term)

        count = len(found_terms)
        if count >= 3:
            verdict = "pass"
            rule_desc = f"Rigorous evaluation framework: detected {count} metrics/benchmarks/datasets ({', '.join(list(found_terms)[:4])})."
        elif count >= 1:
            verdict = "partial"
            rule_desc = f"Moderate evaluation framework: detected {count} metric/dataset ({', '.join(found_terms)})."
        else:
            verdict = "fail"
            rule_desc = "No explicit metrics, datasets, or experimental testbeds detected in literature corpus."

        confidence = "high" if count >= 2 else "medium"
        return PhDQualificationCriterion(
            criterion_name="rigorous",
            verdict=verdict,
            numbers={"detected_terms": sorted(list(found_terms)), "count": count},
            rule_description=rule_desc,
            confidence=confidence,
        )

    def evaluate_feasible(
        self,
        cluster: UnsolvedProblemCluster,
        matching_papers: List[CorpusPaper],
    ) -> PhDQualificationCriterion:
        """(5) Feasible: open code or datasets referenced, no proprietary-only signal."""
        combined_text = " ".join([c.claim_text for c in cluster.quoted_claims]).lower()
        for paper in matching_papers:
            combined_text += " " + (paper.title or "").lower() + " " + (paper.url or "").lower()
            combined_text += " " + (paper.abstract or "").lower()
            for sec_text in paper.full_text_sections.values():
                combined_text += " " + sec_text.lower()

        has_open = any(re.search(rf"\b{re.escape(k)}\b", combined_text) for k in OPEN_ARTIFACTS_KEYWORDS)
        has_prop = any(re.search(rf"\b{re.escape(k)}\b", combined_text) for k in PROPRIETARY_KEYWORDS)

        if has_open and not has_prop:
            verdict = "pass"
            rule_desc = "Feasible for PhD execution: open-source code/datasets/repositories referenced with no proprietary blocks."
        elif not has_prop:
            verdict = "partial"
            rule_desc = "Feasible: standard open research environment with no proprietary barriers detected."
        else:
            verdict = "fail"
            rule_desc = "Feasibility risk: relies on proprietary or non-public internal datasets/hardware."

        confidence = "high" if has_open else "medium"
        return PhDQualificationCriterion(
            criterion_name="feasible",
            verdict=verdict,
            numbers={"has_open_artifacts": has_open, "has_proprietary_signal": has_prop},
            rule_description=rule_desc,
            confidence=confidence,
        )

    def evaluate_publishable(
        self,
        cluster: UnsolvedProblemCluster,
        matching_papers: List[CorpusPaper],
    ) -> PhDQualificationCriterion:
        """(6) Publishable: related work appears in configured refereed venues."""
        refereed_matches = []
        for paper in matching_papers:
            v_low = (paper.venue or "").lower()
            if any(k in v_low for k in self.refereed_venues) or (paper.is_oa and paper.venue):
                refereed_matches.append(paper.venue or "Refereed venue")

        count = len(refereed_matches)
        if count >= 2:
            verdict = "pass"
            rule_desc = f"Strong publication potential: {count} related papers published in refereed venues ({', '.join(refereed_matches[:3])})."
        elif count == 1:
            verdict = "partial"
            rule_desc = f"Moderate publication potential: 1 related paper in refereed venue ({refereed_matches[0]})."
        else:
            verdict = "fail"
            rule_desc = "Limited evidence of publication in high-impact refereed venues."

        confidence = "high" if count >= 2 else "medium"
        return PhDQualificationCriterion(
            criterion_name="publishable",
            verdict=verdict,
            numbers={"refereed_count": count, "venues": refereed_matches[:5]},
            rule_description=rule_desc,
            confidence=confidence,
        )

    def assess_qualification(
        self,
        cluster: UnsolvedProblemCluster,
        corpus_papers: List[CorpusPaper],
        professor_corpus: Optional[ProfessorCorpus] = None,
    ) -> PhDQualificationResult:
        """Evaluates all 6 PhD criteria and determines overall outcome."""
        matching_papers = [
            p for p in corpus_papers
            if p.paper_id in cluster.papers or any(p.title in claim.supporting_span for claim in cluster.quoted_claims)
        ]
        if not matching_papers:
            matching_papers = corpus_papers

        # Check for insufficient evidence upfront
        if (
            (professor_corpus and professor_corpus.insufficient_corpus)
            or len(corpus_papers) < 2
        ):
            c1 = self.evaluate_original(cluster)
            c2 = self.evaluate_significant(cluster, matching_papers)
            c3 = self.evaluate_doctoral_scope(cluster)
            c4 = self.evaluate_rigorous(cluster, matching_papers)
            c5 = self.evaluate_feasible(cluster, matching_papers)
            c6 = self.evaluate_publishable(cluster, matching_papers)

            criteria_map = {
                "original": c1,
                "significant": c2,
                "doctoral_scope": c3,
                "rigorous": c4,
                "feasible": c5,
                "publishable": c6,
            }
            return PhDQualificationResult(
                problem_id=cluster.cluster_id,
                outcome="insufficient_evidence",
                criteria=criteria_map,
                summary_reason=f"Insufficient evidence: corpus has only {len(corpus_papers)} paper(s). Minimum threshold is 20.",
            )

        c1 = self.evaluate_original(cluster)
        c2 = self.evaluate_significant(cluster, matching_papers)
        c3 = self.evaluate_doctoral_scope(cluster)
        c4 = self.evaluate_rigorous(cluster, matching_papers)
        c5 = self.evaluate_feasible(cluster, matching_papers)
        c6 = self.evaluate_publishable(cluster, matching_papers)

        criteria_map = {
            "original": c1,
            "significant": c2,
            "doctoral_scope": c3,
            "rigorous": c4,
            "feasible": c5,
            "publishable": c6,
        }

        # Count verdicts
        passes = sum(1 for c in criteria_map.values() if c.verdict == "pass")
        partials = sum(1 for c in criteria_map.values() if c.verdict == "partial")
        total_qualifying = passes + partials

        # Default outcome rule: criteria 1 (original) and 3 (doctoral_scope) pass and 4 of 6 overall pass/partial
        if c1.verdict == "pass" and c3.verdict == "pass" and total_qualifying >= 4:
            outcome = "qualified"
            reason = f"Qualified: Originality and Doctoral Scope passed with {passes} pass criteria and {partials} partial criteria."
        elif (c1.verdict in ("pass", "partial")) and (c3.verdict in ("pass", "partial")) and total_qualifying >= 3:
            outcome = "borderline"
            reason = f"Borderline: Partial alignment on core criteria with {total_qualifying} total qualifying criteria."
        else:
            outcome = "rejected"
            reason = f"Rejected: Failed core PhD criteria (Originality verdict: {c1.verdict}, Scope verdict: {c3.verdict})."

        return PhDQualificationResult(
            problem_id=cluster.cluster_id,
            outcome=outcome,
            criteria=criteria_map,
            summary_reason=reason,
        )
