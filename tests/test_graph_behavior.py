import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import graph_behavior


@pytest.fixture(autouse=True)
def isolated_graph(tmp_path, monkeypatch):
    monkeypatch.setattr(graph_behavior, "GRAPH_FILE", tmp_path / "behavior_graph.json")
    monkeypatch.setattr(graph_behavior, "OLD_HISTORY", tmp_path / "move_history.json")
    yield


def test_query_returns_empty_list_when_no_graph():
    result = graph_behavior.query(r"C:\Users\xboxf\Downloads\syllabus.pdf")
    assert result == []


def test_record_then_query_returns_destination():
    graph_behavior.record(
        r"C:\Users\xboxf\Downloads\syllabus.pdf",
        r"C:\Users\xboxf\Documents\ASU"
    )
    result = graph_behavior.query(r"C:\Users\xboxf\Downloads\syllabus.pdf")
    paths = [r[0] for r in result]
    assert r"C:\Users\xboxf\Documents\ASU" in paths


def test_more_moves_score_higher():
    for _ in range(5):
        graph_behavior.record(
            r"C:\Users\xboxf\Downloads\invoice.pdf",
            r"C:\Users\xboxf\Documents\Finance"
        )
    graph_behavior.record(
        r"C:\Users\xboxf\Downloads\invoice.pdf",
        r"C:\Users\xboxf\Documents\Other"
    )
    result = graph_behavior.query(r"C:\Users\xboxf\Downloads\invoice.pdf")
    assert result[0][0] == r"C:\Users\xboxf\Documents\Finance"


def test_query_returns_at_most_three():
    for i in range(5):
        graph_behavior.record(
            r"C:\Users\xboxf\Downloads\doc.pdf",
            rf"C:\Users\xboxf\Documents\Folder{i}"
        )
    result = graph_behavior.query(r"C:\Users\xboxf\Downloads\doc.pdf")
    assert len(result) <= 3


def test_query_result_is_list_of_tuples():
    graph_behavior.record(
        r"C:\Users\xboxf\Downloads\resume.pdf",
        r"C:\Users\xboxf\Documents\Career"
    )
    result = graph_behavior.query(r"C:\Users\xboxf\Downloads\resume.pdf")
    assert all(isinstance(r, tuple) and len(r) == 2 for r in result)


def test_migration_from_move_history_json(tmp_path, monkeypatch):
    monkeypatch.setattr(graph_behavior, "GRAPH_FILE", tmp_path / "behavior_graph.json")
    old = tmp_path / "move_history.json"
    monkeypatch.setattr(graph_behavior, "OLD_HISTORY", old)
    old.write_text(json.dumps({
        ".pdf": {r"C:\Users\xboxf\Documents\ASU": 7}
    }), encoding="utf-8")

    graph_behavior._migrate()

    assert not old.exists()
    result = graph_behavior.query(r"C:\Users\xboxf\Downloads\anything.pdf")
    assert any(r[0] == r"C:\Users\xboxf\Documents\ASU" for r in result)
