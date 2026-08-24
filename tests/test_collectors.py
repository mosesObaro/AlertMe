"""Tests for discovery collectors with mock responses."""

import pytest
from src.models import ItemType
from src.collectors.arxiv import ArxivCollector
from src.collectors.openalex import OpenAlexCollector, reconstruct_abstract_from_inverted_index
from src.collectors.crossref import clean_crossref_abstract
from src.collectors.conferences import ConferenceCollector
from src.collectors.opportunities import OpportunityCollector


SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2608.12345v1</id>
    <published>2026-08-24T12:00:00Z</published>
    <title>Dynamic Offloading for Edge Intelligence</title>
    <summary>We propose an edge computing scheduler for latency optimization.</summary>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Johnson</name></author>
    <arxiv:doi>10.1109/EDGE.2026.01</arxiv:doi>
    <category term="cs.DC"/>
  </entry>
</feed>"""


def test_arxiv_collector_parse():
    collector = ArxivCollector()
    items = collector._parse_feed(SAMPLE_ARXIV_XML)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Dynamic Offloading for Edge Intelligence"
    assert item.arxiv_id == "2608.12345v1"
    assert item.doi == "10.1109/EDGE.2026.01"
    assert len(item.authors) == 2
    assert "cs.DC" in item.topics


def test_openalex_abstract_reconstruction():
    inv_idx = {
        "Edge": [0],
        "computing": [1],
        "enables": [2],
        "low": [3],
        "latency": [4],
        "inference": [5]
    }
    abstract = reconstruct_abstract_from_inverted_index(inv_idx)
    assert abstract == "Edge computing enables low latency inference"


def test_clean_crossref_abstract():
    raw_xml = "<jats:p>We investigate <jats:italic>computation offloading</jats:italic> in MEC.</jats:p>"
    clean = clean_crossref_abstract(raw_xml)
    assert clean == "We investigate computation offloading in MEC."


def test_conference_collector_deadlines():
    conf_config = [
        {
            "name": "ACM Symposium on Edge Computing",
            "acronym": "SEC",
            "typical_deadline_month": 12,
            "topics": ["Edge Computing", "Edge AI"],
            "website": "https://acm-ieee-sec.org"
        }
    ]
    collector = ConferenceCollector(conferences_config=conf_config, cfp_feeds=[])
    items = collector.fetch()
    assert isinstance(items, list)
