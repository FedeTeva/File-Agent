import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import graph_context


def test_returns_empty_string_when_both_graphs_empty():
    with patch("graph_context.graph_behavior.query", return_value=[]), \
         patch("graph_context.graph_semantic.query", return_value=[]):
        result = graph_context.get_context(r"C:\Users\xboxf\Downloads\file.pdf")
    assert result == ""


def test_includes_behavioral_section_when_results_exist():
    with patch("graph_context.graph_behavior.query", return_value=[
        (r"C:\Users\xboxf\Documents\ASU", 8)
    ]), patch("graph_context.graph_semantic.query", return_value=[]):
        result = graph_context.get_context(r"C:\Users\xboxf\Downloads\syllabus.pdf")
    assert "Behavioral patterns" in result
    assert r"C:\Users\xboxf\Documents\ASU" in result
    assert "x8" in result


def test_includes_semantic_section_when_results_exist():
    with patch("graph_context.graph_behavior.query", return_value=[]), \
         patch("graph_context.graph_semantic.query", return_value=[
             (r"C:\Users\xboxf\Documents\Finance", ["invoice", "billing"])
         ]):
        result = graph_context.get_context(r"C:\Users\xboxf\Downloads\invoice.pdf")
    assert "Semantic context" in result
    assert r"C:\Users\xboxf\Documents\Finance" in result
    assert "invoice" in result


def test_includes_both_sections_when_both_have_results():
    with patch("graph_context.graph_behavior.query", return_value=[
        (r"C:\Users\xboxf\Documents\ASU", 5)
    ]), patch("graph_context.graph_semantic.query", return_value=[
        (r"C:\Users\xboxf\Documents\ASU", ["coursework"])
    ]):
        result = graph_context.get_context(r"C:\Users\xboxf\Downloads\hw.pdf")
    assert "Behavioral patterns" in result
    assert "Semantic context" in result


def test_passes_file_name_and_empty_preview_to_semantic_query():
    with patch("graph_context.graph_behavior.query", return_value=[]), \
         patch("graph_context.graph_semantic.query", return_value=[]) as mock_sem:
        graph_context.get_context(r"C:\Users\xboxf\Downloads\report.pdf")
    mock_sem.assert_called_once_with("report.pdf", "")
