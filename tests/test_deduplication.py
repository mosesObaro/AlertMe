"""Tests for multi-stage academic deduplication engine."""

import pytest
from src.models import ResearchItem, ItemType
from src.deduplication.deduplicator import (
    Deduplicator, normalize_doi, normalize_arxiv_id, normalize_url, normalize_title, title_similarity
)


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1109/TMC.2026.12345") == "10.1109/tmc.2026.12345"
    assert normalize_doi("http://dx.doi.org/10.1145/3345.6789") == "10.1145/3345.6789"
    assert normalize_doi("10.1007/s10586-026-0456-7") == "10.1007/s10586-026-0456-7"
    assert normalize_doi(None) is None


def test_normalize_arxiv_id():
    assert normalize_arxiv_id("2301.12345v2") == "2301.12345"
    assert normalize_arxiv_id("arXiv:2405.09876v1") == "2405.09876"
    assert normalize_arxiv_id("cs.DC/0102003") == "cs.DC/0102003".lower()


def test_normalize_url():
    assert normalize_url("https://www.example.com/paper?utm_source=feed&id=1") == "example.com/paper"
    assert normalize_url("http://example.com/paper/") == "example.com/paper"


def test_title_similarity():
    t1 = "Adaptive Computation Offloading for Edge AI in 6G Networks"
    t2 = "Adaptive Computation Offloading for Edge AI in 6G Networks: An Optimization Approach"
    t3 = "Unrelated Quantum Computing Approaches"

    sim_high = title_similarity(t1, t2)
    sim_low = title_similarity(t1, t3)

    assert sim_high > 0.75
    assert sim_low < 0.3


def test_deduplicator_catches_doi_and_arxiv_duplicates():
    dedup = Deduplicator()

    item1 = ResearchItem(
        title="Edge Intelligence Architecture",
        url="https://arxiv.org/abs/2601.0001",
        source="arXiv",
        doi="10.1109/TMC.2026.9999",
        arxiv_id="2601.0001v1",
        abstract="Abstract from arXiv"
    )

    item2 = ResearchItem(
        title="Edge Intelligence Architecture (IEEE Version)",
        url="https://ieeexplore.ieee.org/document/9999",
        source="Crossref",
        doi="10.1109/TMC.2026.9999",
        abstract="Richer abstract from IEEE with more details"
    )

    unique = dedup.deduplicate([item1, item2])
    assert len(unique) == 1
    assert unique[0].doi == "10.1109/TMC.2026.9999"


def test_deduplicator_merges_metadata():
    dedup = Deduplicator()

    item1 = ResearchItem(
        title="Federated Learning at Edge",
        url="https://arxiv.org/abs/2602.0002",
        source="arXiv",
        authors=["Author A"],
        abstract="Initial abstract"
    )

    item2 = ResearchItem(
        title="Federated Learning at Edge",
        url="https://doi.org/10.1145/12345",
        source="ACM",
        authors=["Author A", "Author B", "Author C"],
        doi="10.1145/12345",
        venue="ACM SEC"
    )

    unique = dedup.deduplicate([item1, item2])
    assert len(unique) == 1
    # Merged item should have richer author list and venue
    assert len(unique[0].authors) == 3
    assert unique[0].venue == "ACM SEC"
    assert unique[0].doi == "10.1145/12345"
