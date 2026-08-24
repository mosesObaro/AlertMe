"""Tests for configuration loading and environment variable expansion."""

import os
import pytest
from src.utils.config_loader import ConfigManager, load_yaml_file


def test_config_loader_reads_topics():
    manager = ConfigManager()
    assert len(manager.primary_topics) > 0
    assert "Edge Computing" in manager.primary_topics
    assert "Edge AI" in manager.primary_topics
    assert len(manager.secondary_topics) > 0
    assert len(manager.research_topics) > 0
    assert "Computation Offloading" in manager.research_topics
    assert len(manager.negative_keywords) > 0


def test_config_loader_reads_profile():
    manager = ConfigManager()
    assert manager.phd_target.get("field") == "Edge Computing"
    assert manager.learning_stage.get("current_level") is not None
    assert isinstance(manager.learning_stage.get("current_topics"), list)
    assert manager.alert_thresholds.get("minimum_score") is not None


def test_env_var_expansion(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_RECIPIENT", "custom_phd@university.edu")
    test_yaml = tmp_path / "test.yaml"
    test_yaml.write_text("recipient: ${TEST_RECIPIENT:-default@example.com}\nfallback: ${MISSING_VAR:-default_val}\n")
    
    data = load_yaml_file(test_yaml)
    assert data["recipient"] == "custom_phd@university.edu"
    assert data["fallback"] == "default_val"
