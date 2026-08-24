"""Tests for persistent JSON state management and dashboard generation."""

import pytest
import json
from src.models import ResearchItem, ScoreBreakdown
from src.storage.state_manager import StateManager
from src.storage.dashboard_generator import DashboardGenerator


def test_state_manager_seen_items(tmp_path):
    sm = StateManager(data_dir=tmp_path)
    assert len(sm.load_seen_ids()) == 0

    item = ResearchItem(
        title="Test Edge Paper",
        url="https://example.com/test",
        source="IEEE",
        doi="10.1109/test.123",
        arxiv_id="2601.9999"
    )

    sm.record_seen_items([item])
    seen = sm.load_seen_ids()
    assert item.id in seen
    assert "doi_10.1109/test.123" in seen
    assert "arxiv_2601.9999" in seen


def test_state_manager_alert_history(tmp_path):
    sm = StateManager(data_dir=tmp_path)
    item = ResearchItem(
        title="Test Alert",
        url="https://example.com/alert",
        source="Crossref"
    )
    item.score = ScoreBreakdown(final_score=8.5)

    sm.record_alerts_sent([item], alert_mode="daily")
    history = sm.load_alert_history()
    assert len(history) == 1
    assert history[0]["title"] == "Test Alert"
    assert history[0]["alert_mode"] == "daily"


def test_dashboard_generator(tmp_path):
    sm = StateManager(data_dir=tmp_path)
    gen = DashboardGenerator(state_manager=sm)

    item = ResearchItem(
        title="Dashboard Test Paper",
        url="https://example.com/paper",
        source="ACM"
    )
    item.score = ScoreBreakdown(final_score=9.0)

    gen.generate_dashboard_data([item], trends=[], supervisors=[])
    dashboard_file = gen.state_manager.data_dir.parent / "docs" / "data.json"
    if not dashboard_file.exists():
        # check default docs dir
        import src.storage.dashboard_generator as dg
        dashboard_file = dg.DASHBOARD_DATA_FILE

    assert dashboard_file.exists()
    with open(dashboard_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "meta" in data
        assert "items" in data
