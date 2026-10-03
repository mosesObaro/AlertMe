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

def test_llm_extractor_structured_mock(tmp_path, sample_research_item):
    from src.research_gaps.gap_extractor import GapExtractor
    from src.research_gaps.models import ExtractionMethod, Confidence
    from src.research_gaps.llm_client import AnthropicClient

    mock_client = MagicMock(spec=AnthropicClient)
    mock_client.is_available.return_value = True
    mock_client.call_structured.return_value = {
        "scoped_problem": "Dynamic task offloading frameworks fail to sustain performance under severe energy consumption constraints.",
        "research_question": "How can dynamic offloading maintain latency bounds despite battery energy consumption constraints?",
        "why_unresolved": "Interference creates unmodeled state transitions.",
        "limitations": [
            {
                "claim_text": "Battery energy degradation is unconsidered",
                "supporting_span": "The limitation is that this work does not consider energy consumption",
            }
        ],
        "open_questions": [
            {
                "claim_text": "Extension to federated learning scenarios",
                "supporting_span": "Future work will extend to federated learning scenarios",
            }
        ],
        "existing_approaches": ["Static heuristic schedulers"],
        "candidate_methods": ["Deep reinforcement learning actor-critic"],
        "evaluation_metrics": ["latency", "energy"],
    }

    extractor = GapExtractor(cache_dir=tmp_path / "cache", llm_client=mock_client)
    res = extractor.extract(sample_research_item)

    assert res.extraction_method == ExtractionMethod.LLM
    assert res.confidence == Confidence.NORMAL
    assert res.research_problem == "Dynamic task offloading frameworks fail to sustain performance under severe energy consumption constraints."
    assert len(res.limitations) == 1
    assert res.limitations[0].supporting_span == "The limitation is that this work does not consider energy consumption"
    assert len(res.future_work) == 1
    assert res.future_work[0].supporting_span == "Future work will extend to federated learning scenarios"
    assert res.existing_approaches == ["Static heuristic schedulers"]
    assert res.candidate_methods == ["Deep reinforcement learning actor-critic"]


def test_extractor_model_not_found_raises_immediately(tmp_path, sample_research_item):
    from src.research_gaps.gap_extractor import GapExtractor
    from src.research_gaps.llm_client import AnthropicClient, ModelNotFoundError

    mock_client = MagicMock(spec=AnthropicClient)
    mock_client.is_available.return_value = True
    mock_client.call_structured.side_effect = ModelNotFoundError("Model claude-sonnet-5-5 not found (404)")

    extractor = GapExtractor(cache_dir=tmp_path / "cache", llm_client=mock_client)
    with pytest.raises(ModelNotFoundError):
        extractor.extract(sample_research_item)

    assert extractor.fallback_count == 0


def test_extractor_transient_error_retries_and_falls_back(tmp_path, sample_research_item):
    from src.research_gaps.gap_extractor import GapExtractor
    from src.research_gaps.models import ExtractionMethod
    from src.research_gaps.llm_client import AnthropicClient, LLMExecutionError

    mock_client = MagicMock(spec=AnthropicClient)
    mock_client.is_available.return_value = True
    mock_client.call_structured.side_effect = LLMExecutionError("API 500 server error")

    extractor = GapExtractor(cache_dir=tmp_path / "cache", llm_client=mock_client)
    res = extractor.extract(sample_research_item)

    # Max retries is 1, so 2 calls made before falling back
    assert mock_client.call_structured.call_count == 2
    assert res.extraction_method == ExtractionMethod.DETERMINISTIC_FALLBACK
    assert extractor.fallback_count == 1


def test_extractor_drops_unsupported_spans(tmp_path, sample_research_item):
    from src.research_gaps.gap_extractor import GapExtractor
    from src.research_gaps.llm_client import AnthropicClient

    mock_client = MagicMock(spec=AnthropicClient)
    mock_client.is_available.return_value = True
    mock_client.call_structured.return_value = {
        "scoped_problem": "Offloading latency bottleneck in edge computing.",
        "research_question": "How to optimize?",
        "why_unresolved": "Complex.",
        "limitations": [
            {
                "claim_text": "Fabricated limitation",
                "supporting_span": "This phrase absolutely does not appear anywhere in the abstract text at all.",
            }
        ],
        "open_questions": [],
        "existing_approaches": ["Heuristics"],
        "candidate_methods": ["Novel DRL framework"],
        "evaluation_metrics": ["latency"],
    }

    extractor = GapExtractor(cache_dir=tmp_path / "cache", llm_client=mock_client)
    res = extractor.extract(sample_research_item)

    assert len(res.limitations) == 0


def test_extractor_flags_low_confidence_when_methods_equal_statement(tmp_path, sample_research_item):
    from src.research_gaps.gap_extractor import GapExtractor
    from src.research_gaps.models import Confidence
    from src.research_gaps.llm_client import AnthropicClient

    mock_client = MagicMock(spec=AnthropicClient)
    mock_client.is_available.return_value = True
    stmt = "Dynamic task offloading in heterogeneous edge environments"
    mock_client.call_structured.return_value = {
        "scoped_problem": stmt,
        "research_question": "How to offload?",
        "why_unresolved": "Hard.",
        "limitations": [],
        "open_questions": [],
        "existing_approaches": ["Baselines"],
        "candidate_methods": [stmt],  # Exact duplication symptom
        "evaluation_metrics": ["latency"],
    }

    extractor = GapExtractor(cache_dir=tmp_path / "cache", llm_client=mock_client)
    res = extractor.extract(sample_research_item)

    assert res.confidence == Confidence.LOW
    assert "candidate_methods_equals_statement" in res.low_confidence_reasons


def test_extractor_cache_roundtrip(tmp_path, sample_research_item):
    from src.research_gaps.gap_extractor import GapExtractor
    from src.research_gaps.llm_client import AnthropicClient

    mock_client = MagicMock(spec=AnthropicClient)
    mock_client.is_available.return_value = True
    mock_client.call_structured.return_value = {
        "scoped_problem": "Dynamic task offloading in heterogeneous edge environments.",
        "research_question": "How to optimize?",
        "why_unresolved": "Hard.",
        "limitations": [],
        "open_questions": [],
        "existing_approaches": ["Baselines"],
        "candidate_methods": ["New algorithm"],
        "evaluation_metrics": ["latency"],
    }

    cache_dir = tmp_path / "cache"
    extractor1 = GapExtractor(cache_dir=cache_dir, llm_client=mock_client)
    res1 = extractor1.extract(sample_research_item)
    assert mock_client.call_structured.call_count == 1

    # Second extractor instance reading from same cache dir
    extractor2 = GapExtractor(cache_dir=cache_dir, llm_client=mock_client)
    res2 = extractor2.extract(sample_research_item)
    # Call count should still be 1 (served from cache)
    assert mock_client.call_structured.call_count == 1
    assert res2.research_problem == res1.research_problem


