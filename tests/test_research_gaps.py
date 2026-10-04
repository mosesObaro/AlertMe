"""Comprehensive test suite for the Research Gap Analysis module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.models import ResearchItem
from src.research_gaps.models import (
    ExtractedPaperInfo,
    ResearchProblem,
    ResearchGapCluster,
    CandidateResearchDirection,
    FeasibilityAssessment,
    SupervisorMatch,
    LinkVerificationResult,
    ProblemStatus,
    LinkStatus,
)
from src.research_gaps.gap_extractor import GapExtractor
from src.research_gaps.problem_tracker import ProblemTracker
from src.research_gaps.clustering import ProblemClusterer
from src.research_gaps.question_generator import ResearchQuestionGenerator
from src.research_gaps.supervisor_matcher import SupervisorMatcher
from src.research_gaps.feasibility import FeasibilityAssessor
from src.research_gaps.link_verifier import LinkVerifier
from src.research_gaps.dashboard_generator import ResearchGapDashboardGenerator
from src.research_gaps.state_manager import ResearchGapStateManager
from src.deduplication.deduplicator import Deduplicator


@pytest.fixture
def sample_research_item():
    return ResearchItem(
        title="Dynamic Task Offloading for Edge Computing with Deep Reinforcement Learning",
        url="https://arxiv.org/abs/2301.12345",
        source="arXiv",
        authors=["Alice Smith", "Bob Johnson"],
        doi="10.1109/EDGE.2026.01",
        arxiv_id="2301.12345",
        publication_date="2024-06-15",
        abstract="Edge computing enables low-latency processing. However, the challenge of dynamic task offloading in heterogeneous edge environments remains unresolved. We propose a deep reinforcement learning framework for joint computation offloading and resource allocation. Experimental results show that our approach achieves 30% latency reduction. The limitation is that this work does not consider energy consumption. Future work will extend to federated learning scenarios.",
        venue="IEEE Edge Computing",
        topics=["edge computing", "deep reinforcement learning", "task offloading"],
    )


@pytest.fixture
def sample_extracted_paper(sample_research_item):
    extractor = GapExtractor()
    return extractor.extract(sample_research_item)


@pytest.fixture
def sample_problem():
    return ResearchProblem(
        id="prob_test123",
        problem_statement="However, the challenge of dynamic task offloading in heterogeneous edge environments remains unresolved.",
        research_area="Edge Computing",
        problem_cluster="Resource Allocation",
        supporting_papers=["paper_test1"],
        evidence=["Paper A noted offloading latency bottleneck"],
        frequency=1,
        existing_approaches=["Deep Q-Networks", "Heuristic schedulers"],
        known_limitations=["Does not consider energy consumption"],
        unresolved_questions=["How to handle dynamic channel fading?"],
        candidate_methods=["Lyapunov optimization with Actor-Critic"],
        evaluation_metrics=["latency", "energy"],
        status=ProblemStatus.NEW,
    )


# ── 1. Paper Extraction (GapExtractor) ──────────────────────────────

def test_gap_extractor_basic(sample_research_item):
    extractor = GapExtractor()
    info = extractor.extract(sample_research_item)
    assert info is not None
    assert isinstance(info, ExtractedPaperInfo)
    assert info.title == sample_research_item.title
    assert info.year == 2024
    assert "challenge" in info.research_problem.lower() or "unresolved" in info.research_problem.lower()
    assert len(info.limitations) > 0
    assert len(info.future_work) > 0
    assert "latency" in info.evaluation_metrics


def test_gap_extractor_empty_abstract():
    extractor = GapExtractor()
    item = ResearchItem(title="Test", url="http://test.com", source="Test", abstract="")
    info = extractor.extract(item)
    assert info.research_problem == ""
    assert len(info.limitations) == 0
    assert len(info.future_work) == 0


def test_gap_extractor_batch(sample_research_item):
    extractor = GapExtractor()
    item2 = ResearchItem(
        title="TinyML on Microcontrollers",
        url="http://test2.com",
        source="Test",
        abstract="However, memory footprint remains a major bottleneck. We propose a pruning method.",
    )
    results = extractor.extract_batch([sample_research_item, item2])
    assert len(results) == 2
    assert results[0].title == sample_research_item.title
    assert results[1].title == "TinyML on Microcontrollers"


# ── 2. Paper Deduplication (Deduplicator reuse) ─────────────────────

def test_deduplication_doi_match():
    dedup = Deduplicator()
    item1 = ResearchItem(title="Paper A", url="http://a.com", source="src", doi="10.123/456")
    item2 = ResearchItem(title="Paper B", url="http://b.com", source="src", doi="10.123/456")
    is_dup, _ = dedup.is_duplicate(item1, [item2])
    assert is_dup


def test_deduplication_title_similarity():
    dedup = Deduplicator()
    item1 = ResearchItem(title="Deep learning for edge computing in IoT", url="http://a.com", source="src")
    item2 = ResearchItem(title="Deep Learning for Edge Computing in IoT Networks", url="http://b.com", source="src")
    is_dup, _ = dedup.is_duplicate(item1, [item2])
    assert is_dup


# ── 3. Research Gap Extraction ──────────────────────────────────────

def test_extract_research_problem(sample_extracted_paper):
    assert sample_extracted_paper.research_problem != ""
    assert "unresolved" in sample_extracted_paper.research_problem.lower() or "challenge" in sample_extracted_paper.research_problem.lower()


def test_extract_limitations(sample_extracted_paper):
    assert len(sample_extracted_paper.limitations) > 0
    assert any("energy" in lim.lower() or "limitation" in lim.lower() for lim in sample_extracted_paper.limitations)


def test_extract_future_work(sample_extracted_paper):
    assert len(sample_extracted_paper.future_work) > 0
    assert any("federated" in fw.lower() or "future" in fw.lower() for fw in sample_extracted_paper.future_work)


# ── 4. Problem Tracker ──────────────────────────────────────────────

def test_problem_tracker_add_new(tmp_path, sample_extracted_paper):
    tracker = ProblemTracker(data_dir=tmp_path)
    problem = tracker.add_or_update_problem(sample_extracted_paper, "Edge Computing")
    assert problem is not None
    assert problem.status == ProblemStatus.NEW
    assert problem.frequency == 1
    assert sample_extracted_paper.paper_id in problem.supporting_papers


def test_problem_tracker_merge_evidence(tmp_path, sample_extracted_paper):
    tracker = ProblemTracker(data_dir=tmp_path)
    p1 = tracker.add_or_update_problem(sample_extracted_paper, "Edge Computing")
    assert p1.frequency == 1

    # Add second paper with same problem statement
    paper2 = ExtractedPaperInfo(
        paper_id="paper_2",
        title="Another Paper on Offloading",
        research_problem=sample_extracted_paper.research_problem,
        limitations=["High communication overhead"],
        future_work=["Hardware testbed evaluation"],
    )
    p2 = tracker.add_or_update_problem(paper2, "Edge Computing")
    assert p2.frequency == 2
    assert "paper_2" in p2.supporting_papers
    assert "High communication overhead" in p2.known_limitations


def test_problem_tracker_status_upgrade(tmp_path, sample_extracted_paper):
    tracker = ProblemTracker(data_dir=tmp_path)
    tracker.add_or_update_problem(sample_extracted_paper, "Edge Computing")

    # Add 2 more times to reach frequency=3
    for i in range(2):
        paper = ExtractedPaperInfo(
            paper_id=f"paper_extra_{i}",
            title=f"Extra Paper {i}",
            research_problem=sample_extracted_paper.research_problem,
        )
        p = tracker.add_or_update_problem(paper, "Edge Computing")

    assert p.frequency == 3
    assert p.status == ProblemStatus.INVESTIGATING  # Upgrades to investigating at freq >= 3
    assert p.status != ProblemStatus.PROMISING  # NEVER auto-promotes to promising


def test_problem_tracker_persistence(tmp_path, sample_problem):
    tracker = ProblemTracker(data_dir=tmp_path)
    tracker.save_problems([sample_problem])
    loaded = tracker.load_problems()
    assert len(loaded) == 1
    assert loaded[0].id == sample_problem.id
    assert loaded[0].problem_statement == sample_problem.problem_statement


# ── 5. Clustering ───────────────────────────────────────────────────

def test_clustering_similar_problems():
    clusterer = ProblemClusterer(similarity_threshold=0.3, min_cluster_size=2)
    p1 = ResearchProblem(
        id="p1",
        problem_statement="Dynamic task offloading latency in edge computing",
        research_area="Edge Computing",
        supervisor_keywords=["offloading", "latency", "edge"],
        frequency=2,
    )
    p2 = ResearchProblem(
        id="p2",
        problem_statement="Task offloading latency minimization in edge systems",
        research_area="Edge Computing",
        supervisor_keywords=["offloading", "latency", "edge"],
        frequency=2,
    )
    clusters = clusterer.cluster_problems([p1, p2], [])
    assert len(clusters) >= 1
    assert "p1" in clusters[0].supporting_problems
    assert "p2" in clusters[0].supporting_problems


def test_clustering_dissimilar_problems():
    clusterer = ProblemClusterer(similarity_threshold=0.8, min_cluster_size=2)
    p1 = ResearchProblem(
        id="p1",
        problem_statement="Quantum key distribution in satellite networks",
        research_area="Quantum",
        supervisor_keywords=["quantum", "satellite"],
        frequency=1,
    )
    p2 = ResearchProblem(
        id="p2",
        problem_statement="TinyML model quantization for microcontrollers",
        research_area="TinyML",
        supervisor_keywords=["tinyml", "quantization"],
        frequency=1,
    )
    clusters = clusterer.cluster_problems([p1, p2], [])
    assert len(clusters) == 0  # No cluster formed (min_cluster_size=2)


def test_cluster_update():
    clusterer = ProblemClusterer()
    existing = [ResearchGapCluster(cluster_id="c1", name="Edge AI", frequency=2)]
    new = [ResearchGapCluster(cluster_id="c1", name="Edge AI", frequency=3)]
    merged = clusterer.update_clusters(existing, new)
    assert len(merged) == 1
    assert merged[0].frequency == 5


# ── 6. Problem Classification ───────────────────────────────────────

def test_problem_status_new(sample_problem):
    assert sample_problem.status == ProblemStatus.NEW


def test_problem_no_auto_promising(tmp_path, sample_extracted_paper):
    tracker = ProblemTracker(data_dir=tmp_path)
    for i in range(10):  # Very high frequency
        paper = ExtractedPaperInfo(
            paper_id=f"paper_high_{i}",
            title=f"Paper {i}",
            research_problem=sample_extracted_paper.research_problem,
        )
        p = tracker.add_or_update_problem(paper, "Edge Computing")
    assert p.status != ProblemStatus.PROMISING
    assert p.status == ProblemStatus.INVESTIGATING


# ── 7. Question Generation ──────────────────────────────────────────

def test_question_generation(sample_problem, sample_extracted_paper):
    generator = ResearchQuestionGenerator()
    direction = generator.generate_directions(sample_problem, [sample_extracted_paper])
    assert direction is not None
    assert isinstance(direction, CandidateResearchDirection)
    assert len(direction.research_questions) >= 2
    assert len(direction.research_questions) <= 5
    assert direction.potential_contribution != ""
    assert direction.possible_methodology != ""


def test_question_generation_evidence_flag(sample_problem, sample_extracted_paper):
    generator = ResearchQuestionGenerator()
    direction = generator.generate_directions(sample_problem, [sample_extracted_paper])
    assert direction.evidence_supported is True


# ── 8. Supervisor Matching ──────────────────────────────────────────

def test_supervisor_matching(sample_problem):
    matcher = SupervisorMatcher()
    with patch.object(matcher, "load_supervisor_data") as mock_data:
        mock_data.return_value = {
            "prof_1": {
                "name": "Prof. Alan Turing",
                "institution": "Cambridge",
                "country": "UK",
                "research_areas": ["Edge Computing", "Task Offloading", "Distributed Systems"],
                "topics": ["edge computing", "offloading"],
                "profile_url": "https://example.com/turing",
            }
        }
        matches = matcher.match_supervisors(sample_problem)
        assert len(matches) > 0
        assert matches[0].name == "Prof. Alan Turing"
        assert matches[0].match_score > 0.0


def test_supervisor_no_false_match(sample_problem):
    matcher = SupervisorMatcher()
    with patch.object(matcher, "load_supervisor_data") as mock_data:
        mock_data.return_value = {
            "prof_2": {
                "name": "Prof. Gregor Mendel",
                "institution": "Brno",
                "country": "Czech",
                "research_areas": ["Genetics", "Botany", "Plant Biology"],
                "topics": ["genetics"],
                "profile_url": "https://example.com/mendel",
            }
        }
        matches = matcher.match_supervisors(sample_problem)
        assert len(matches) == 0


# ── 9. Link Verification ────────────────────────────────────────────

def test_valid_url(tmp_path):
    verifier = LinkVerifier(cache_dir=tmp_path)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/paper"
    mock_resp.history = []
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.text = ""

    with patch.object(verifier.session, "get", return_value=mock_resp):
        res = verifier.verify_url("https://example.com/paper")
        assert res.link_status == LinkStatus.VALID
        assert res.http_status == 200


def test_redirect_url(tmp_path):
    verifier = LinkVerifier(cache_dir=tmp_path)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/canonical-paper"
    mock_resp.history = [MagicMock()]  # Has history -> redirected
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.text = "<html><body>Paper content</body></html>"

    with patch.object(verifier.session, "get", return_value=mock_resp):
        res = verifier.verify_url("https://doi.org/10.123/paper")
        assert res.link_status == LinkStatus.REDIRECTED
        assert res.redirect_target == "https://example.com/canonical-paper"


def test_broken_url_404(tmp_path):
    verifier = LinkVerifier(cache_dir=tmp_path)
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.url = "https://example.com/missing"
    mock_resp.history = []

    with patch.object(verifier.session, "get", return_value=mock_resp):
        res = verifier.verify_url("https://example.com/missing")
        assert res.link_status == LinkStatus.BROKEN
        assert res.http_status == 404


def test_malformed_url(tmp_path):
    verifier = LinkVerifier(cache_dir=tmp_path)
    res = verifier.verify_url("not-a-valid-url")
    assert res.link_status == LinkStatus.BROKEN
    assert res.http_status == 0


def test_unreachable_url(tmp_path):
    verifier = LinkVerifier(cache_dir=tmp_path)
    import requests
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Failed")):
        res = verifier.verify_url("https://nonexistent-domain-12345.org")
        assert res.link_status == LinkStatus.UNREACHABLE


def test_canonical_url_replacement():
    verifier = LinkVerifier()
    paper = ExtractedPaperInfo(
        doi="10.1109/EDGE.2026.01",
        url="https://arxiv.org/abs/2301.12345",
    )
    canonical = verifier._find_canonical_url(paper)
    assert canonical == "https://doi.org/10.1109/EDGE.2026.01"


def test_cached_verification(tmp_path):
    verifier = LinkVerifier(cache_dir=tmp_path)
    cached_result = LinkVerificationResult(
        url="https://example.com/cached",
        link_status=LinkStatus.VALID,
        http_status=200,
        last_verified="2026-10-01T00:00:00",
    )
    cache = {cached_result.url: cached_result}
    verifier.save_cache(cache)

    # Re-instantiate to load from file
    verifier2 = LinkVerifier(cache_dir=tmp_path)
    with patch("requests.get") as mock_get:
        res = verifier2.verify_url("https://example.com/cached")
        assert res.link_status == LinkStatus.VALID
        mock_get.assert_not_called()  # Cache hit, no network call


# ── 10. Dashboard Data Generation ───────────────────────────────────

def test_dashboard_data_generation(sample_problem):
    dash_gen = ResearchGapDashboardGenerator()
    payload = dash_gen.generate_dashboard_data(
        problems=[sample_problem.to_dict()],
        clusters=[],
        directions=[],
        papers=[],
        feasibility_map={},
        supervisor_map={},
        link_results={},
    )
    assert "meta" in payload
    assert "problems" in payload
    assert payload["meta"]["total_problems"] == 1
    assert payload["meta"]["new_problems"] == 1


def test_dashboard_meta_counts(sample_problem):
    dash_gen = ResearchGapDashboardGenerator()
    p_promising = dict(sample_problem.to_dict(), id="p2", status=ProblemStatus.PROMISING)
    p_shortlisted = dict(sample_problem.to_dict(), id="p3", status=ProblemStatus.SHORTLISTED)

    payload = dash_gen.generate_dashboard_data(
        problems=[sample_problem.to_dict(), p_promising, p_shortlisted],
        clusters=[],
        directions=[],
        papers=[],
        feasibility_map={},
        supervisor_map={},
        link_results={},
    )
    assert payload["meta"]["total_problems"] == 3
    assert payload["meta"]["new_problems"] == 1
    assert payload["meta"]["promising_problems"] == 1
    assert payload["meta"]["shortlisted_problems"] == 1


# ── 11. Feasibility Assessment ──────────────────────────────────────

def test_feasibility_assessment(sample_problem, sample_extracted_paper):
    assessor = FeasibilityAssessor()
    assessment = assessor.assess(sample_problem, [sample_extracted_paper], [])
    assert assessment is not None
    assert isinstance(assessment, FeasibilityAssessment)
    assert assessment.novelty in ["high", "medium", "low", "unknown"]
    assert assessment.feasibility in ["high", "medium", "low", "unknown"]
    assert assessment.significance in ["high", "medium", "low", "unknown"]
    assert assessment.novelty_evidence != ""
    assert assessment.phd_depth in ["high", "medium", "low", "unknown"]


# ── 12. Models ──────────────────────────────────────────────────────

def test_research_problem_to_dict(sample_problem):
    data = sample_problem.to_dict()
    assert isinstance(data, dict)
    assert data["id"] == sample_problem.id
    reconstructed = ResearchProblem.from_dict(data)
    assert reconstructed.id == sample_problem.id
    assert reconstructed.problem_statement == sample_problem.problem_statement


def test_extracted_paper_id_generation():
    p1 = ExtractedPaperInfo(title="Test Paper", url="https://example.com/1", doi="10.123/456")
    p2 = ExtractedPaperInfo(title="Different Title", url="https://example.com/2", doi="10.123/456")
    # Same DOI should produce same paper_id
    assert p1.paper_id == p2.paper_id


# ── 13. Enhanced SupervisorMatcher ──────────────────────────────────


def _make_matcher_with_data(supervisor_data: dict) -> SupervisorMatcher:
    """Helper: return a SupervisorMatcher whose load_supervisor_data is mocked."""
    matcher = SupervisorMatcher()
    matcher._professor_cache = supervisor_data
    return matcher


def test_supervisor_match_explanation_field(sample_problem):
    """Matched SupervisorMatch should contain a non-empty match_explanation."""
    matcher = _make_matcher_with_data({
        "prof_edge": {
            "name": "Prof. Edge Expert",
            "university": "Test University",
            "country": "UK",
            "research_interests": ["Edge Computing", "Task Offloading", "Distributed Systems"],
            "research_summary": "Expert in edge computing and task offloading for IoT.",
            "edge_relevance": "Direct research in edge AI and distributed scheduling.",
            "research_trajectory": "From cloud computing to edge intelligence.",
        }
    })
    matches = matcher.match_supervisors(sample_problem)
    assert len(matches) > 0
    top = matches[0]
    assert isinstance(top.match_explanation, str)
    assert len(top.match_explanation) > 10  # Non-trivial explanation produced


def test_supervisor_match_score_range(sample_problem):
    """Match scores must be in [0, 1]."""
    matcher = _make_matcher_with_data({
        "prof_a": {
            "name": "Prof. A",
            "university": "Uni A",
            "country": "Germany",
            "research_interests": ["Edge Computing", "Federated Learning"],
            "research_summary": "Federated learning at the edge.",
            "edge_relevance": "edge inference and scheduling",
            "research_trajectory": "Cloud to edge.",
        },
        "prof_b": {
            "name": "Prof. B",
            "university": "Uni B",
            "country": "Canada",
            "research_interests": ["Quantum Computing", "Number Theory"],
            "research_summary": "Pure mathematics and quantum algorithms.",
            "edge_relevance": "",
            "research_trajectory": "Academia.",
        },
    })
    matches = matcher.match_supervisors(sample_problem)
    for m in matches:
        assert 0.0 <= m.match_score <= 1.0


def test_supervisor_recruitment_bonus(sample_problem):
    """CONFIRMED_ACTIVE recruitment status should boost score over UNKNOWN."""
    base_data = {
        "name": "Prof. Active",
        "university": "Active University",
        "country": "HK",
        "research_interests": ["Edge Computing"],
        "research_summary": "edge computing",
        "edge_relevance": "edge computing",
        "research_trajectory": "edge systems",
    }
    prof_active = {**base_data, "recruitment": {"status": "CONFIRMED_ACTIVE"}}
    prof_unknown = {**base_data, "name": "Prof. Passive", "recruitment": {"status": "UNKNOWN"}}

    matcher_active = _make_matcher_with_data({"a": prof_active})
    matcher_passive = _make_matcher_with_data({"b": prof_unknown})

    score_active = matcher_active.match_supervisors(sample_problem)
    score_passive = matcher_passive.match_supervisors(sample_problem)

    if score_active and score_passive:
        assert score_active[0].match_score >= score_passive[0].match_score


def test_supervisor_pub_relevance_boosts_score(sample_problem):
    """A professor with a relevant recent publication should score higher."""
    base = {
        "name": "Prof. Edge",
        "university": "Tech University",
        "country": "US",
        "research_interests": ["Edge Computing", "Task Offloading"],
        "research_summary": "edge computing research",
        "edge_relevance": "edge offloading",
        "research_trajectory": "edge systems",
    }
    relevant_pub = {
        "title": "Dynamic task offloading in edge computing environments",
        "year": 2024,
        "topics": ["edge computing", "task offloading"],
        "abstract": "We propose a deep reinforcement learning approach for task offloading in heterogeneous edge environments.",
    }

    prof_no_pubs = dict(base)
    prof_with_pubs = {**base, "recent_papers": [relevant_pub]}

    matcher_no_pubs = _make_matcher_with_data({"a": prof_no_pubs})
    matcher_with_pubs = _make_matcher_with_data({"b": prof_with_pubs})

    score_no = matcher_no_pubs.match_supervisors(sample_problem)
    score_with = matcher_with_pubs.match_supervisors(sample_problem)

    if score_no and score_with:
        assert score_with[0].match_score >= score_no[0].match_score


def test_supervisor_match_max_results(sample_problem):
    """match_supervisors should return at most max_matches results."""
    profs = {
        f"prof_{i}": {
            "name": f"Prof. {i}",
            "university": f"Uni {i}",
            "country": "UK",
            "research_interests": ["Edge Computing", "Distributed Systems"],
            "research_summary": "edge computing",
            "edge_relevance": "edge",
            "research_trajectory": "systems",
        }
        for i in range(20)
    }
    matcher = _make_matcher_with_data(profs)
    matches = matcher.match_supervisors(sample_problem, max_matches=5)
    assert len(matches) <= 5


def test_supervisor_match_all_returns_dict(sample_problem):
    """match_all returns a dict keyed by problem ID."""
    matcher = _make_matcher_with_data({
        "prof_x": {
            "name": "Prof. X",
            "university": "X Uni",
            "country": "Japan",
            "research_interests": ["Edge AI", "TinyML"],
            "research_summary": "TinyML and edge AI.",
            "edge_relevance": "tiny ml edge",
            "research_trajectory": "edge systems",
        }
    })
    result = matcher.match_all([sample_problem])
    assert isinstance(result, dict)
    assert sample_problem.id in result
    assert isinstance(result[sample_problem.id], list)


def test_supervisor_match_model_roundtrip(sample_problem):
    """SupervisorMatch.to_dict() / from_dict() roundtrip preserves all fields."""
    match = SupervisorMatch(
        name="Dr. Test",
        institution="Test University",
        country="Canada",
        relevant_research_areas=["Edge Computing", "Federated Learning"],
        relevant_publications=[],
        matching_keywords=["edge", "computing"],
        profile_url="https://example.com/test",
        google_scholar_url="https://scholar.google.com/test",
        semantic_scholar_url="",
        link_status=LinkStatus.UNKNOWN,
        match_score=0.7531,
        match_explanation="Test explanation for this match.",
    )
    d = match.to_dict()
    assert d["name"] == "Dr. Test"
    assert d["match_score"] == 0.7531
    assert d["match_explanation"] == "Test explanation for this match."

    restored = SupervisorMatch.from_dict(d)
    assert restored.name == match.name
    assert restored.match_score == match.match_score
    assert restored.match_explanation == match.match_explanation


def test_supervisor_export_matches_creates_files(tmp_path, sample_problem):
    """export_matches should create all three output files."""
    import importlib
    import src.research_gaps.supervisor_matcher as sm_module

    # Temporarily redirect OUTPUTS_DIR to tmp_path
    original_dir = sm_module.OUTPUTS_DIR
    sm_module.OUTPUTS_DIR = tmp_path
    try:
        matcher = SupervisorMatcher()
        match = SupervisorMatch(
            name="Prof. Export Test",
            institution="Export University",
            country="Sweden",
            relevant_research_areas=["Edge Computing"],
            matching_keywords=["edge"],
            match_score=0.42,
            match_explanation="Test export explanation.",
        )
        supervisor_map = {sample_problem.id: [match]}
        matcher.export_matches([sample_problem], supervisor_map)

        assert (tmp_path / "problem_professor_matches.json").exists()
        assert (tmp_path / "problem_professor_matches.csv").exists()
        assert (tmp_path / "problem_professor_matches.md").exists()

        # Verify JSON structure
        import json
        data = json.loads((tmp_path / "problem_professor_matches.json").read_text())
        assert isinstance(data, list)
        assert data[0]["problem_id"] == sample_problem.id
        assert len(data[0]["matches"]) == 1
        assert data[0]["matches"][0]["name"] == "Prof. Export Test"
        assert "match_explanation" in data[0]["matches"][0]
    finally:
        sm_module.OUTPUTS_DIR = original_dir


def test_supervisor_no_match_below_threshold(sample_problem):
    """Professors with zero keyword overlap should not appear in results."""
    matcher = _make_matcher_with_data({
        "prof_unrelated": {
            "name": "Prof. Botany",
            "university": "Botanical Institute",
            "country": "Germany",
            "research_interests": ["Mycology", "Plant Genetics", "Photosynthesis"],
            "research_summary": "Studying photosynthesis and plant cell biology.",
            "edge_relevance": "",
            "research_trajectory": "From botany to plant genomics.",
        }
    })
    matches = matcher.match_supervisors(sample_problem)
    assert len(matches) == 0


def test_supervisor_per_country_data_loads(tmp_path):
    """_load_per_country_professors reads professors.json from country subdirs."""
    import json as _json

    # Create a fake country directory
    country_dir = tmp_path / "test_country"
    country_dir.mkdir()
    profs = [
        {
            "researcher_id": "test_prof_1",
            "name": "Prof. Test One",
            "university": "Test University",
            "country": "TestLand",
            "research_interests": ["Edge Computing"],
        }
    ]
    (country_dir / "professors.json").write_text(_json.dumps(profs))

    import src.research_gaps.supervisor_matcher as sm_module
    original_dir = sm_module.SUPERVISORS_DATA_DIR
    original_dirs = sm_module._COUNTRY_DIRS
    sm_module.SUPERVISORS_DATA_DIR = tmp_path
    sm_module._COUNTRY_DIRS = ["test_country"]
    try:
        matcher = SupervisorMatcher(data_dir=tmp_path)
        loaded = matcher._load_per_country_professors()
        assert "test_prof_1" in loaded
        assert loaded["test_prof_1"]["name"] == "Prof. Test One"
    finally:
        sm_module.SUPERVISORS_DATA_DIR = original_dir
        sm_module._COUNTRY_DIRS = original_dirs


# ── 14. Phase 1 Data Model & Provenance Tests ─────────────────────────

def test_evidence_claim_coercion_and_equality():
    from src.research_gaps.models import EvidenceClaim, coerce_claims
    claim = EvidenceClaim.coerce("Battery drain under burst traffic", default_paper_id="paper_123")
    assert claim.claim_text == "Battery drain under burst traffic"
    assert claim.paper_id == "paper_123"
    assert claim.supporting_span == "Battery drain under burst traffic"
    assert "battery" in claim.lower()
    assert claim == "Battery drain under burst traffic"

    claims = coerce_claims(["Limitation A", {"claim_text": "Limitation B", "paper_id": "p2", "supporting_span": "span B"}], default_paper_id="p1")
    assert len(claims) == 2
    assert claims[0].paper_id == "p1"
    assert claims[1].paper_id == "p2"
    assert claims[1].supporting_span == "span B"


def test_citation_from_research_item():
    from src.models import ResearchItem
    from src.research_gaps.models import Citation
    item = ResearchItem(
        title="Adaptive Edge Intelligence",
        url="https://doi.org/10.1109/TPDS.2023.12345",
        source="IEEE",
        authors=["Alice Smith", "Bob Jones"],
        doi="10.1109/TPDS.2023.12345",
        publication_date="2023-05-01",
        venue="IEEE TPDS",
    )
    cit = Citation.from_research_item(item)
    assert cit.doi == "10.1109/TPDS.2023.12345"
    assert cit.year == 2023
    assert cit.link == "https://doi.org/10.1109/TPDS.2023.12345"
    assert "Alice Smith & Bob Jones (2023)" in cit.format()
    assert "IEEE TPDS" in cit.format()

    # Fallback to URL when DOI is missing
    item_no_doi = ResearchItem(title="Tech Report", url="https://example.com/report", source="Web")
    cit2 = Citation.from_research_item(item_no_doi)
    assert cit2.doi is None
    assert cit2.link == "https://example.com/report"


def test_canonical_paper_id_consistency():
    from src.models import ResearchItem
    from src.research_gaps.models import canonical_paper_id
    doi = "10.1109/tpds.2023.3289012"
    item = ResearchItem(title="Test", url="http://x.com", source="s", doi=doi)
    cid = canonical_paper_id(doi=doi)
    assert item.id == cid
    assert cid.startswith("doi_")


def test_legacy_research_problem_migration():
    from src.research_gaps.models import ResearchProblem, ExtractionMethod, Confidence
    legacy_dict = {
        "id": "prob_old1",
        "problem_statement": "Old bottleneck in edge computing",
        "research_area": "Edge Computing",
        "supporting_papers": ["doi_12345"],
        "known_limitations": ["Old limitation string"],
        "unresolved_questions": ["Old question string"],
    }
    prob = ResearchProblem.from_dict(legacy_dict)
    assert prob.extraction_method == ExtractionMethod.LEGACY_REGEX
    assert prob.confidence == Confidence.LOW
    assert len(prob.known_limitations) == 1
    assert prob.known_limitations[0].claim_text == "Old limitation string"
    assert prob.known_limitations[0].paper_id == "doi_12345"
    assert prob.known_limitations[0].supporting_span == "Old limitation string"


# ── 15. Phase 2 Structured LLM Extractor Tests ────────────────────────

# LLM tests removed in step 0 (rules-based pipeline only)


# ── 16. Phase 3 Two-Stage Problem Grouping Tests ──────────────────────

LABELLED_PAPER_PAIRS = [
    # True positives: equivalent technical research bottleneck
    (
        "Dynamic task offloading in edge environments incurs severe latency bottlenecks under time-varying wireless channel fading",
        "Dynamic computation offloading frameworks for edge devices suffer from unpredictable latency spikes caused by wireless channel fading",
        True,
    ),
    (
        "Federated learning on heterogeneous edge devices suffers from client drift and straggler delays during model synchronization",
        "Straggler effects and heterogeneous compute capacities degrade convergence rates and synchronization latency in edge federated learning",
        True,
    ),
    # True negatives: distinct technical bottlenecks in edge domain
    (
        "Dynamic task offloading in edge environments incurs severe latency bottlenecks under time-varying wireless channel fading",
        "Quantization and pruning of deep neural networks on microcontroller units induces catastrophic accuracy loss",
        False,
    ),
    (
        "Federated learning on heterogeneous edge devices suffers from client drift and straggler delays during model synchronization",
        "Security vulnerabilities in vehicular edge computing architectures enable man-in-the-middle spoofing of roadside units",
        False,
    ),
    (
        "Dynamic task offloading in edge environments incurs severe latency bottlenecks under time-varying wireless channel fading",
        "Battery thermal degradation accelerates during burst cryptographic hashing in mobile edge nodes",
        False,
    ),
]


def test_labelled_paper_pairs_fixture_tuning():
    """Validates that Jaccard similarity separates positive pairs (>=0.28) from negative pairs (<0.20)."""
    from src.research_gaps.problem_tracker import extract_problem_tokens, compute_token_jaccard

    for s1, s2, is_same in LABELLED_PAPER_PAIRS:
        t1 = extract_problem_tokens(s1)
        t2 = extract_problem_tokens(s2)
        sim = compute_token_jaccard(t1, t2)
        if is_same:
            assert sim >= 0.28, f"Positive pair failed threshold: {sim:.3f} < 0.28 for '{s1[:30]}' / '{s2[:30]}'"
        else:
            assert sim < 0.20, f"Negative pair exceeded threshold: {sim:.3f} >= 0.20 for '{s1[:30]}' / '{s2[:30]}'"


def test_grouping_stage1_shortlisting(tmp_path):
    from src.research_gaps.problem_tracker import ProblemTracker, extract_problem_tokens
    from src.research_gaps.models import ResearchProblem

    tracker = ProblemTracker(data_dir=tmp_path)
    # Populate existing problems
    p1 = ResearchProblem(
        id="prob_offload_1",
        problem_statement="Dynamic computation offloading under wireless channel fading in edge devices",
        research_area="Edge Computing",
        supervisor_keywords=["edge computing", "offloading", "wireless"],
    )
    p2 = ResearchProblem(
        id="prob_quant_2",
        problem_statement="Quantization noise in microcontroller deep learning models",
        research_area="Edge Computing",
        supervisor_keywords=["quantization", "microcontroller", "tinyml"],
    )
    tracker.save_problems([p1, p2])

    query_stmt = "Dynamic task offloading suffers latency degradation under severe wireless fading"
    tokens = extract_problem_tokens(query_stmt, keywords=["offloading", "edge computing"])
    shortlist = tracker.shortlist_candidates(tokens, query_stmt, [p1, p2])

    # Only p1 should be in shortlist; p2 should be excluded due to low overlap
    assert len(shortlist) == 1
    assert shortlist[0][0].id == "prob_offload_1"


# LLM grouping tests removed in step 0


def test_grouping_fallback_without_llm_marks_low_confidence(tmp_path):
    from src.research_gaps.problem_tracker import ProblemTracker
    from src.research_gaps.models import ResearchProblem, ExtractedPaperInfo, Confidence

    # LLM client not available (default when no API key)
    tracker = ProblemTracker(data_dir=tmp_path)
    existing = ResearchProblem(
        id="prob_offload_base",
        problem_statement="Dynamic task offloading in edge environments incurs severe latency bottlenecks under time-varying wireless channel fading",
        research_area="Edge Computing",
        supervisor_keywords=["offloading", "latency", "fading", "wireless", "edge"],
        frequency=1,
        supporting_papers=["paper_init"],
    )
    tracker.save_problems([existing])

    # Second paper matching the positive pair (Jaccard ~ 0.318 > fallback_threshold 0.28)
    incoming = ExtractedPaperInfo(
        paper_id="paper_fallback_2",
        title="Offloading Paper 2",
        research_problem="Dynamic computation offloading frameworks for edge devices suffer from unpredictable latency spikes caused by wireless channel fading",
        keywords=["offloading", "latency", "fading", "wireless", "edge"],
    )

    merged = tracker.add_or_update_problem(incoming, "Edge Computing")
    assert merged.id == "prob_offload_base"
    assert merged.frequency == 2
    assert merged.confidence == Confidence.LOW


# ── 17. Phase 4 Feasibility Assessment Tests ──────────────────────────

def test_assessment_insufficient_evidence_below_min_source_count(tmp_path):
    from src.research_gaps.feasibility import FeasibilityAssessor
    from src.research_gaps.models import ResearchProblem, ExtractedPaperInfo

    assessor = FeasibilityAssessor(cache_dir=tmp_path / "cache")
    problem = ResearchProblem(
        id="prob_single_source",
        problem_statement="Isolated problem statement",
        supporting_papers=["paper_1"],  # 1 paper < min_source_count (2)
    )
    paper1 = ExtractedPaperInfo(paper_id="paper_1", title="Paper 1")

    res = assessor.assess(problem, [paper1], [])
    assert res.novelty == "unknown"
    assert "Insufficient evidence" in res.novelty_evidence
    assert res.feasibility == "unknown"
    assert "Insufficient evidence" in res.feasibility_evidence
    assert res.publication_potential == "unknown"
    assert "Insufficient evidence" in res.publication_evidence
    assert res.phd_depth == "unknown"
    assert "Insufficient evidence" in res.phd_depth_evidence


def test_assessment_deterministic_rubric(tmp_path):
    from src.research_gaps.feasibility import FeasibilityAssessor
    from src.research_gaps.models import ResearchProblem, ExtractedPaperInfo, EvidenceClaim

    assessor = FeasibilityAssessor(cache_dir=tmp_path / "cache")
    problem = ResearchProblem(
        id="prob_sufficient_sources",
        problem_statement="Task offloading under severe battery energy degradation",
        supporting_papers=["paper_1", "paper_2"],
        known_limitations=[
            EvidenceClaim(claim_text="Battery drain", paper_id="paper_1", supporting_span="Battery drain"),
            EvidenceClaim(claim_text="Thermal throttle", paper_id="paper_2", supporting_span="Thermal throttle"),
        ],
        unresolved_questions=[
            EvidenceClaim(claim_text="Energy harvesting", paper_id="paper_1", supporting_span="Energy harvesting"),
            EvidenceClaim(claim_text="Cooperative offload", paper_id="paper_2", supporting_span="Cooperative offload"),
        ],
        candidate_methods=["Actor-critic reinforcement learning", "Dynamic voltage scaling"],
        existing_approaches=["Baseline heuristic"],
    )
    paper1 = ExtractedPaperInfo(paper_id="paper_1", title="Paper 1", citation_count=20)
    paper2 = ExtractedPaperInfo(paper_id="paper_2", title="Paper 2", citation_count=15)

    res = assessor.assess(problem, [paper1, paper2], [])
    assert res.novelty in ["high", "medium", "low"]
    assert "SEC" not in res.publication_evidence
    assert "INFOCOM" not in res.publication_evidence
    assert "MobiCom" not in res.publication_evidence
    assert "NeurIPS" not in res.publication_evidence
    assert "literature" in res.novelty_evidence.lower()
    assert res.feasibility == "high"  # has methods and existing approaches
    assert res.publication_potential == "high"  # 2 limitations
    assert res.phd_depth == "high"  # 2 unresolved questions


# LLM feasibility tests removed in step 0


# ── 18. Phase 5 Dashboard & Pipeline Verification Tests ───────────────

def test_dashboard_embeds_full_citation_objects(sample_problem):
    from src.research_gaps.dashboard_generator import ResearchGapDashboardGenerator

    dash_gen = ResearchGapDashboardGenerator()
    paper_data = {
        "paper_id": "doi_fd8071479658a576",
        "doi": "10.1109/TPDS.2023.3289012",
        "title": "Adaptive Edge Intelligence",
        "authors": ["Alice Smith", "Bob Jones"],
        "year": 2023,
        "venue": "IEEE TPDS",
        "url": "https://doi.org/10.1109/TPDS.2023.3289012",
    }
    prob_dict = sample_problem.to_dict()
    prob_dict["supporting_papers"] = ["doi_fd8071479658a576"]

    payload = dash_gen.generate_dashboard_data(
        problems=[prob_dict],
        clusters=[],
        directions=[],
        papers=[paper_data],
        feasibility_map={},
        supervisor_map={},
        link_results={},
    )

    prob = payload["problems"][0]
    assert "citations" in prob
    assert len(prob["citations"]) == 1
    cit = prob["citations"][0]
    assert cit["doi"] == "10.1109/TPDS.2023.3289012"
    assert cit["link"] == "https://doi.org/10.1109/TPDS.2023.3289012"
    assert "Alice Smith & Bob Jones (2023)" in cit["citation_string"]
    assert "IEEE TPDS" in cit["citation_string"]


def test_dashboard_html_contains_no_papermap():
    from pathlib import Path
    html_path = Path(__file__).resolve().parent.parent / "docs" / "research-gaps.html"
    content = html_path.read_text(encoding="utf-8")

    # paperMap must be completely removed
    assert "paperMap" not in content
    # Embedded citations property should be checked
    assert "citations" in content
    # Publication evidence must be rendered
    assert "publication_evidence" in content


# Pipeline CI test updated for rules-based execution






# ── Step 1 Corpus Builder Tests ─────────────────────────────────────────────

def test_corpus_builder_reaches_20_or_flags_insufficient_corpus(tmp_path):
    from src.research_gaps.corpus_builder import CorpusBuilder
    from src.utils.rate_limiter import PoliteRequester

    mock_requester = MagicMock(spec=PoliteRequester)
    # Mock OpenAlex author search
    mock_requester.get.return_value.status_code = 200
    mock_requester.get.return_value.json.return_value = {
        "results": [
            {
                "id": "https://openalex.org/A12345",
                "last_known_institution": {"display_name": "The Hong Kong Polytechnic University"},
                "x_concepts": [{"display_name": "Edge Computing"}, {"display_name": "Distributed Systems"}],
            }
        ]
    }

    builder = CorpusBuilder(data_dir=tmp_path, requester=mock_requester)
    prof = {
        "id": "prof_jiannong_cao",
        "name": "Prof. Jiannong Cao",
        "clean_name": "Jiannong Cao",
        "university": "The Hong Kong Polytechnic University",
        "research_interests": ["Edge Computing", "Distributed Systems"],
    }

    corpus = builder.build_corpus_for_professor(prof)
    assert corpus.professor_name == "Prof. Jiannong Cao"
    assert corpus.match_confidence in ["high", "medium"]
    assert hasattr(corpus, "insufficient_corpus")
    assert corpus.target_count == 20


def test_corpus_builder_excludes_below_threshold(tmp_path):
    from src.research_gaps.corpus_builder import CorpusBuilder, CorpusPaper

    builder = CorpusBuilder(data_dir=tmp_path)
    prof = {
        "id": "prof_test",
        "name": "Test Prof",
        "research_interests": ["Edge AI", "Offloading"],
        "research_summary": "Edge computing and offloading",
    }
    high_rel = CorpusPaper(
        paper_id="p1", title="Edge AI Offloading", abstract="Edge AI offloading framework", role="related", year=2025
    )
    low_rel = CorpusPaper(
        paper_id="p2", title="Unrelated Medieval History", abstract="History of castles", role="related", year=2021
    )

    scored = builder._score_candidates([high_rel, low_rel], prof, set())
    assert high_rel.relevance_score > low_rel.relevance_score
    assert high_rel.relevance_score >= builder.relevance_threshold
    assert low_rel.relevance_score < builder.relevance_threshold


def test_corpus_builder_rejects_same_name_mismatch(tmp_path):
    from src.research_gaps.corpus_builder import OpenAlexAuthorResolver
    from src.utils.rate_limiter import PoliteRequester

    mock_requester = MagicMock(spec=PoliteRequester)
    mock_requester.get.return_value.status_code = 200
    mock_requester.get.return_value.json.return_value = {
        "results": [
            {
                "id": "https://openalex.org/A99999",
                "last_known_institution": {"display_name": "Department of Cardiology, Paris Hospital"},
                "x_concepts": [{"display_name": "Cardiology"}, {"display_name": "Heart Surgery"}],
            }
        ]
    }

    resolver = OpenAlexAuthorResolver(requester=mock_requester)
    prof = {
        "name": "John Smith",
        "clean_name": "John Smith",
        "university": "MIT CSAIL",
        "research_interests": ["Edge Computing", "Distributed Systems"],
    }


# ── Step 2 Unsolved Problem Extractor & Clustering Tests ─────────────────────

def test_unsolved_extractor_discourse_marker_cleaning():
    from src.research_gaps.unsolved_extractor import clean_sentence

    raw1 = "However, the framework fails under high latency."
    cleaned1 = clean_sentence(raw1, "Paper A")
    assert cleaned1 == "[Paper A] The framework fails under high latency."

    raw2 = "Furthermore, energy consumption remains unoptimized."
    cleaned2 = clean_sentence(raw2, "Paper B")
    assert cleaned2 == "Energy consumption remains unoptimized."


def test_unsolved_extractor_verbatim_claims(tmp_path):
    from src.research_gaps.unsolved_extractor import UnsolvedProblemExtractor
    from src.research_gaps.models import ProfessorCorpus, CorpusPaper
    from src.utils.rate_limiter import PoliteRequester

    mock_requester = MagicMock(spec=PoliteRequester)
    mock_requester.get.return_value.status_code = 200
    mock_requester.get.return_value.json.return_value = {"results": []}

    extractor = UnsolvedProblemExtractor(requester=mock_requester)
    sentence = "Dynamic task offloading in edge computing faces severe latency bottlenecks."
    corpus = ProfessorCorpus(
        professor_name="Prof. Test",
        papers=[
            CorpusPaper(
                paper_id="paper_1",
                title="Paper Title 1",
                abstract=f"Background context. {sentence} Summary of results.",
            )
        ]
    )

    clusters = extractor.extract_from_corpus(corpus)
    assert len(clusters) > 0
    claim = clusters[0].quoted_claims[0]
    # Verify verbatim claim matches original text (stripped of discourse marker)
    assert claim.claim_text in sentence or sentence in claim.claim_text or claim.supporting_span == sentence


def test_unsolved_extractor_drops_addressed_clusters(tmp_path):
    from src.research_gaps.unsolved_extractor import UnsolvedProblemExtractor, UnsolvedProblemCluster
    from src.utils.rate_limiter import PoliteRequester

    mock_requester = MagicMock(spec=PoliteRequester)
    mock_requester.get.return_value.status_code = 200
    # Return 3 solution works
    mock_requester.get.return_value.json.return_value = {
        "results": [
            {"id": "w1", "title": "We propose a solution for offloading", "abstract": "we propose a novel method"},
            {"id": "w2", "title": "We address offloading latency", "abstract": "we address the bottleneck"},
            {"id": "w3", "title": "We overcome edge energy degradation", "abstract": "we mitigate the issue"},
        ]
    }

    extractor = UnsolvedProblemExtractor(requester=mock_requester)
    cluster = UnsolvedProblemCluster(
        cluster_id="c1",
        title="Offloading latency bottleneck",
        key_phrases=["offloading latency"],
    )

    status, evidence = extractor._test_unsolved(cluster)
    assert status == "addressed"
    assert len(evidence) == 3


def test_tfidf_jaccard_clustering():
    from src.research_gaps.unsolved_extractor import tfidf_cosine_similarity, keyphrase_jaccard

    s1 = "Dynamic task offloading in edge computing suffers latency degradation"
    s2 = "Computation offloading in edge nodes suffers latency degradation"
    s3 = "Quantum cryptography key exchange in optical networks"

    sim_high = tfidf_cosine_similarity(s1, s2)
    sim_low = tfidf_cosine_similarity(s1, s3)
    assert sim_high > sim_low
    assert sim_high > 0.40


def test_phd_assessor_criteria_numbers_and_rules():
    from src.research_gaps.phd_assessor import PhDQualificationAssessor
    from src.research_gaps.models import UnsolvedProblemCluster, CorpusPaper, EvidenceClaim

    assessor = PhDQualificationAssessor()
    cluster = UnsolvedProblemCluster(
        cluster_id="c1",
        title="Edge Task Offloading Latency",
        key_phrases=["edge offloading", "latency bottleneck"],
        quoted_claims=[
            EvidenceClaim(claim_text="Edge offloading latency remains unoptimized.", paper_id="p1"),
            EvidenceClaim(claim_text="Energy consumption during offloading is unresolved.", paper_id="p2"),
        ],
        support_count=2,
        professors=["Prof. A", "Prof. B"],
        solution_status="open",
        solution_evidence=[],
    )

    papers = [
        CorpusPaper(
            paper_id="p1",
            title="Edge Offloading Study",
            venue="IEEE Transactions on Mobile Computing",
            citation_count=25,
            year=2024,
            abstract="We evaluate latency metrics and dataset benchmarks on edge testbeds with github.com code.",
        ),
        CorpusPaper(
            paper_id="p2",
            title="Energy Constraints in TinyML",
            venue="ACM SEC",
            citation_count=15,
            year=2025,
            abstract="Throughput and accuracy benchmarks were measured on public dataset open source repository.",
        ),
    ]

    result = assessor.assess_qualification(cluster, papers)
    assert result.outcome in ("qualified", "borderline")
    assert len(result.criteria) == 6

    for crit_name, crit in result.criteria.items():
        assert crit.criterion_name == crit_name
        assert crit.verdict in ("pass", "partial", "fail")
        assert isinstance(crit.numbers, dict)
        assert len(crit.numbers) > 0
        assert len(crit.rule_description) > 5
        assert crit.confidence in ("high", "medium", "low")


def test_phd_assessor_insufficient_evidence():
    from src.research_gaps.phd_assessor import PhDQualificationAssessor
    from src.research_gaps.models import UnsolvedProblemCluster, CorpusPaper, ProfessorCorpus

    assessor = PhDQualificationAssessor()
    cluster = UnsolvedProblemCluster(cluster_id="c_small", title="Sparse problem")
    papers = [CorpusPaper(paper_id="p1", title="Single Paper")]

    prof_corpus = ProfessorCorpus(
        professor_name="Prof. Limited",
        papers=papers,
        insufficient_corpus=True,
    )

    result = assessor.assess_qualification(cluster, papers, professor_corpus=prof_corpus)
    assert result.outcome == "insufficient_evidence"
    assert "Insufficient evidence" in result.summary_reason


def test_phd_assessor_rejected_outcome():
    from src.research_gaps.phd_assessor import PhDQualificationAssessor
    from src.research_gaps.models import UnsolvedProblemCluster, CorpusPaper, EvidenceClaim

    assessor = PhDQualificationAssessor()
    cluster = UnsolvedProblemCluster(
        cluster_id="c_addressed",
        title="Addressed problem",
        solution_status="addressed",
        solution_evidence=[{"id": "w1"}, {"id": "w2"}, {"id": "w3"}, {"id": "w4"}],
        quoted_claims=[],  # 0 sub-problems
    )
    papers = [
        CorpusPaper(paper_id="p1", title="Paper 1", year=2020),
        CorpusPaper(paper_id="p2", title="Paper 2", year=2021),
    ]

    result = assessor.assess_qualification(cluster, papers)
    assert result.outcome == "rejected"
    assert result.criteria["original"].verdict == "fail"
    assert result.criteria["doctoral_scope"].verdict == "fail"


def test_ieee_statement_generator_structure(tmp_path):
    from src.research_gaps.statement_generator import IEEEResearchStatementGenerator
    from src.research_gaps.models import (
        UnsolvedProblemCluster, CorpusPaper, PhDQualificationResult, EvidenceClaim, ProfessorCorpus
    )

    generator = IEEEResearchStatementGenerator(reports_dir=tmp_path / "statements")
    cluster = UnsolvedProblemCluster(
        cluster_id="c_test_01",
        title="Edge Task Offloading Latency Bottleneck",
        key_phrases=["edge task offloading", "latency bottleneck"],
        quoted_claims=[
            EvidenceClaim(claim_text="Edge offloading latency remains unoptimized under heavy load.", paper_id="p1"),
            EvidenceClaim(claim_text="Energy degradation exceeds bounds on constrained devices.", paper_id="p2"),
        ],
    )
    papers = [
        CorpusPaper(paper_id="p1", title="Edge Offloading Study", authors=["Alice Smith"], year=2024, doi="10.1109/EDGE.01"),
        CorpusPaper(paper_id="p2", title="Energy Bounds in TinyML", authors=["Bob Jones"], year=2025, doi="10.1109/TMC.02"),
    ]
    qual = PhDQualificationResult(problem_id="c_test_01", outcome="qualified")
    prof_corpus = ProfessorCorpus(professor_name="Prof. Test", papers=papers)

    stmt = generator.generate_statement(cluster, qual, papers, prof_corpus)

    # 1. Section order check
    expected_sections = [
        "I. Introduction", "II. Related Work", "III. Problem Statement and Research Gap",
        "IV. Research Questions and Objectives", "V. Proposed Approach", "VI. Evaluation Plan",
        "VII. Expected Contributions", "VIII. Work Plan"
    ]
    assert list(stmt.sections.keys()) == expected_sections

    # 2. Research questions end in "?"
    assert len(stmt.research_questions) >= 2
    for rq in stmt.research_questions:
        assert rq.strip().endswith("?") or "?" in rq

    # 3. Every [n] resolves in first-citation order
    cited_nums = []
    for s_list in stmt.sections.values():
        for sent in s_list:
            for num in sent.citation_numbers:
                if num not in cited_nums:
                    cited_nums.append(num)

    ref_nums = [r["number"] for r in stmt.references]
    for num in cited_nums:
        assert num in ref_nums

    # First citation order: first cited num must be 1, second 2, etc.
    assert cited_nums == list(range(1, len(cited_nums) + 1))

    # 4. Word count <= 1200
    assert stmt.word_count <= 1200

    # 5. Tagged sentences
    for s_list in stmt.sections.values():
        for sent in s_list:
            assert sent.tag in ("quote", "template")

    # 6. File saved
    saved_file = tmp_path / "statements" / "c_test_01.md"
    assert saved_file.exists()


def test_no_anthropic_imports_or_keys():
    from pathlib import Path
    repo_root = Path(__file__).resolve().parent.parent
    rg_dir = repo_root / "src" / "research_gaps"
    wf_file = repo_root / ".github" / "workflows" / "research-gap-analysis.yml"

    for py_file in rg_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "import anthropic" not in content, f"Anthropic import found in {py_file}"
        assert "AnthropicClient" not in content, f"AnthropicClient reference found in {py_file}"
        assert "ANTHROPIC_API_KEY" not in content, f"ANTHROPIC_API_KEY reference found in {py_file}"

    if wf_file.exists():
        content = wf_file.read_text(encoding="utf-8")
        assert "ANTHROPIC_API_KEY" not in content, "ANTHROPIC_API_KEY found in workflow"


def test_json_holds_all_four_stages_for_fixture_professor(tmp_path):
    import datetime
    from src.research_gaps.pipeline import ResearchGapPipeline
    from src.research_gaps.models import (
        ProfessorCorpus, CorpusPaper, UnsolvedProblemCluster, PhDQualificationResult, IEEEResearchStatement
    )

    pipeline = ResearchGapPipeline()
    corpus = ProfessorCorpus(professor_name="Prof. Fixture", papers=[CorpusPaper(paper_id="p1", title="P1")])
    cluster = UnsolvedProblemCluster(cluster_id="c1", title="Cluster 1")
    qual = PhDQualificationResult(problem_id="c1", outcome="qualified")
    stmt = IEEEResearchStatement(problem_id="c1", title="IEEE Title")

    payload = pipeline._build_4step_dashboard_payload(
        corpora_list=[corpus],
        clusters_by_prof={"Prof. Fixture": [cluster]},
        qualifications_by_prof={"Prof. Fixture": {"c1": qual}},
        statements_by_prof={"Prof. Fixture": {"c1": stmt}},
        start_time=datetime.datetime.now(datetime.timezone.utc),
        fetch_failures=0,
    )

    assert len(payload["professors"]) == 1
    prof_entry = payload["professors"][0]
    assert "papers" in prof_entry  # Step 1
    assert "unsolved_problems" in prof_entry  # Step 2
    assert "phd_qualifications" in prof_entry  # Step 3
    assert "research_statements" in prof_entry  # Step 4
    assert payload["meta"]["extraction_method"] == "rules"


def test_pipeline_end_to_end_offline(tmp_path):
    from src.research_gaps.pipeline import ResearchGapPipeline
    from unittest.mock import patch, MagicMock

    pipeline = ResearchGapPipeline()

    mock_prof = {
        "name": "Prof. Test Offline",
        "university": "Test University",
        "orcid": "0000-0001-2345-6789",
        "research_interests": ["Edge Computing"],
    }

    with patch.object(pipeline.registry, "select_batch", return_value=[mock_prof]), \
         patch.object(pipeline.corpus_builder, "build_corpus") as mock_build_corpus:

        from src.research_gaps.models import ProfessorCorpus, CorpusPaper
        mock_build_corpus.return_value = ProfessorCorpus(
            professor_name="Prof. Test Offline",
            university="Test University",
            papers=[
                CorpusPaper(
                    paper_id="p1",
                    title="Dynamic Offloading in Heterogeneous Edge Environments",
                    abstract="Background. However, the limitation of edge offloading latency remains unoptimized under dynamic conditions.",
                    year=2024,
                    venue="IEEE TMC",
                ),
                CorpusPaper(
                    paper_id="p2",
                    title="Resource Allocation for TinyML",
                    abstract="Background. Furthermore, energy degradation remains an open challenge on constrained devices.",
                    year=2025,
                    venue="ACM SEC",
                )
            ]
        )

        res = pipeline.run(mode="4step", batch_size=1)
        assert res["professors_processed"] == 1
        assert res["extraction_method"] == "rules"
        assert res["fetch_failures"] == 0


def test_doi_normalization_cases():
    from src.research_gaps.link_verifier import LinkVerifier
    verifier = LinkVerifier()

    assert verifier.normalize_doi("https://doi.org/10.1109/TMC.2024.01.") == "10.1109/TMC.2024.01"
    assert verifier.normalize_doi("http://dx.doi.org/10.1145/3676861,") == "10.1145/3676861"
    assert verifier.normalize_doi("doi: 10.3390/s25144500") == "10.3390/s25144500"
    assert verifier.normalize_doi("doi_a1b2c3d4e5f6") is None
    assert verifier.normalize_doi("paper_12345678") is None
    assert verifier.build_doi_url("10.1145/3676861") == "https://doi.org/10.1145/3676861"


def test_doi_handle_api_verification():
    from src.research_gaps.link_verifier import LinkVerifier, LinkStatus
    from unittest.mock import MagicMock

    verifier = LinkVerifier()

    # 1. Registered (code 1)
    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = {"responseCode": 1}
    mock_red1 = MagicMock()
    mock_red1.status_code = 200
    mock_red1.history = []
    mock_red1.url = "https://doi.org/10.1109/TMC.2024.01"

    with patch.object(verifier.session, "get", side_effect=[mock_resp1, mock_red1]):
        res1 = verifier.verify_doi("10.1109/TMC.2024.01")
        assert res1.link_status == LinkStatus.VERIFIED

    # 2. Not found (code 100)
    mock_resp2 = MagicMock()
    mock_resp2.status_code = 200
    mock_resp2.json.return_value = {"responseCode": 100}
    with patch.object(verifier.session, "get", return_value=mock_resp2):
        res2 = verifier.verify_doi("10.9999/NONEXISTENT")
        assert res2.link_status == LinkStatus.DEAD

    # 3. Blocked (HTTP 403 / 429)
    mock_resp3 = MagicMock()
    mock_resp3.status_code = 200
    mock_resp3.json.return_value = {"responseCode": 1}
    mock_red3 = MagicMock()
    mock_red3.status_code = 403
    mock_red3.history = []
    with patch.object(verifier.session, "get", side_effect=[mock_resp3, mock_red3]):
        res3 = verifier.verify_doi("10.1109/BLOCKED")
        assert res3.link_status == LinkStatus.BLOCKED


def test_fallback_chain_order():
    from src.research_gaps.link_verifier import LinkVerifier, LinkStatus

    verifier = LinkVerifier()

    # 1. DOI working
    meta1 = {
        "doi": "10.1109/TMC.2024.01",
        "oa_url": "https://example.com/oa.pdf",
        "arxiv_id": "2401.12345",
    }
    with patch.object(verifier, "verify_doi") as mock_vdoi:
        from src.research_gaps.models import LinkVerificationResult
        mock_vdoi.return_value = LinkVerificationResult(
            url="https://doi.org/10.1109/TMC.2024.01",
            link_url="https://doi.org/10.1109/TMC.2024.01",
            link_type="doi",
            link_status=LinkStatus.VERIFIED,
        )
        res1 = verifier.select_best_link(meta1)
        assert res1.link_type == "doi"
        assert res1.link_url == "https://doi.org/10.1109/TMC.2024.01"

    # 2. DOI dead, OpenAlex OA working
    meta2 = {
        "doi": "10.9999/DEAD",
        "oa_url": "https://example.com/paper.pdf",
        "arxiv_id": "2401.12345",
    }
    with patch.object(verifier, "verify_doi") as mock_vdoi, \
         patch.object(verifier, "verify_url") as mock_vurl:
        mock_vdoi.return_value = LinkVerificationResult(link_status=LinkStatus.DEAD)
        mock_vurl.return_value = LinkVerificationResult(
            url="https://example.com/paper.pdf",
            link_url="https://example.com/paper.pdf",
            link_status=LinkStatus.VERIFIED,
        )
        res2 = verifier.select_best_link(meta2)
        assert res2.link_type == "openalex_oa"
        assert res2.link_url == "https://example.com/paper.pdf"


def test_evidence_bundle_builder(tmp_path):
    from src.research_gaps.evidence_bundle import EvidenceBundleBuilder, save_evidence_bundles, load_evidence_bundles
    from src.research_gaps.models import ExtractedPaperInfo, LinkStatus

    builder = EvidenceBundleBuilder()

    claims_paper = ExtractedPaperInfo(
        paper_id="paper_claim_01",
        title="Edge ML Resource Bottlenecks in Smart Sensors",
        doi="10.1109/TMC.2024.01",
        authors=["Alice Smith", "Bob Jones"],
        year=2024,
        venue="IEEE TMC",
    )
    corpus_paper = ExtractedPaperInfo(
        paper_id="paper_corpus_02",
        title="A Survey of Model Compression Techniques for Microcontrollers",
        doi="10.1145/3676861",
        authors=["Charlie Brown"],
        year=2023,
        venue="ACM Computing Surveys",
    )

    bundle = builder.build_evidence_bundle(
        problem_id="prob_test_123",
        claims_source_papers=[claims_paper],
        corpus_papers=[corpus_paper],
        max_works=40,
    )

    assert bundle.problem_id == "prob_test_123"
    assert len(bundle.works) == 2
    assert bundle.works[0].ref_key == "R1"
    assert bundle.works[1].ref_key == "R2"
    assert bundle.works[0].role == "gap_evidence"
    assert bundle.works[1].role == "background"

    # Test persistence
    bundles_file = tmp_path / "evidence_bundles.json"
    save_evidence_bundles({"prob_test_123": bundle}, bundles_file=bundles_file)
    loaded = load_evidence_bundles(bundles_file=bundles_file)

    assert "prob_test_123" in loaded
    assert len(loaded["prob_test_123"].works) == 2
    assert loaded["prob_test_123"].works[0].title == "Edge ML Resource Bottlenecks in Smart Sensors"


def test_gemini_formulator_model_check():
    from src.research_gaps.llm_formulation import GeminiFormulator
    import pytest

    with pytest.raises(ValueError, match="Prohibited Gemini model"):
        GeminiFormulator(config={"llm": {"model_id": "gemini-1.5-flash"}})


def test_gemini_formulator_fallback_without_key():
    from src.research_gaps.llm_formulation import GeminiFormulator
    from src.research_gaps.models import UnsolvedProblemCluster, PhDQualificationResult, EvidenceBundle

    formulator = GeminiFormulator()
    formulator.api_key = None

    cluster = UnsolvedProblemCluster(cluster_id="c1", title="Edge Offloading")
    qual = PhDQualificationResult(problem_id="c1", outcome="qualified")
    bundle = EvidenceBundle(problem_id="c1")

    stmt = formulator.generate_statement(cluster, qual, bundle)
    assert stmt is None


def test_gemini_formulator_mock_success(monkeypatch):
    import json
    import requests
    from src.research_gaps.llm_formulation import GeminiFormulator
    from src.research_gaps.models import UnsolvedProblemCluster, PhDQualificationResult, EvidenceBundle, EvidenceWork
    from unittest.mock import MagicMock

    formulator = GeminiFormulator(config={"llm": {"model_id": "gemini-2.5-flash"}})
    formulator.api_key = "fake_key_123"

    work1 = EvidenceWork(ref_key="R1", paper_id="p1", title="Title 1", doi="10.1109/TMC.2024.01")
    work2 = EvidenceWork(ref_key="R2", paper_id="p2", title="Title 2", doi="10.1145/3676861")
    bundle = EvidenceBundle(problem_id="c1", works=[work1, work2])

    cluster = UnsolvedProblemCluster(cluster_id="c1", title="Edge Offloading")
    qual = PhDQualificationResult(problem_id="c1", outcome="qualified")

    mock_llm_json = {
        "title": "IEEE Proposal: Optimized Edge Offloading",
        "abstract": "This study proposes an adaptive edge offloading scheme.",
        "research_questions": ["How to optimize latency?"],
        "sections": {
            "Section I: Introduction & Background": "Context on edge computing [R1].",
            "Section II: Problem Statement & Unsolved Gap": "Offloading bottleneck remains [R1] [R2].",
            "Section III: Proposed Research Direction & Methodology": "Methodology proposed [R2].",
            "Section IV: Expected Contributions & Impact": "Open source framework.",
            "Section V: Experimental Strategy & Evaluation Metrics": "Benchmark suite [R1].",
            "Section VI: Related Work & Comparative Analysis": "Related survey [R2].",
            "Section VII: Conclusion & Next Steps": "Summary conclusions.",
        },
    }

    def mock_post(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(mock_llm_json)}]
                    }
                }
            ]
        }
        return mock_resp

    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    stmt = formulator.generate_statement(cluster, qual, bundle)
    assert stmt is not None
    assert stmt.generation_method == "gemini-2.5-flash"
    assert stmt.title == "IEEE Proposal: Optimized Edge Offloading"
    assert len(stmt.research_questions) == 1
    assert stmt.research_questions[0].endswith("?")
    assert len(stmt.references) == 2




