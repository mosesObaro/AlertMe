"""Tests for CLI arguments and debugging commands."""

import pytest
import sys
from unittest.mock import patch
from src.cli import debug_score, main


def test_cli_debug_score(capsys):
    test_args = [
        "cli.py", "debug-score",
        "--title", "Adaptive Computation Offloading for Edge AI in 6G Networks",
        "--abstract", "We propose an energy-efficient computation offloading scheme for MEC.",
        "--source", "IEEE Transactions on Mobile Computing"
    ]
    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    assert "RELEVANCE SCORING DEBUGGER" in captured.out
    assert "Adaptive Computation Offloading" in captured.out
    assert "FINAL RELEVANCE SCORE" in captured.out
    assert "DECISION:" in captured.out
