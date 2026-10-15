import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import graph_semantic


@pytest.fixture(autouse=True)
def isolated_files(tmp_path, monkeypatch):
    monkeypatch.setattr(graph_semantic, "SEMANTIC_INDEX", tmp_path / "semantic_index.json")
    monkeypatch.setattr(graph_semantic, "SCAN_ROOT", str(tmp_path / "Documents"))
    yield tmp_path


def test_query_returns_empty_when_no_index():
    result = graph_semantic.query("invoice.pdf", "")
    assert result == []


def test_query_returns_matching_folder(isolated_files):
    index = {
        r"C:\Users\xboxf\Documents\Finance": {
            "topics": ["invoice", "finance", "billing"],
            "file_count": 10
        },
        r"C:\Users\xboxf\Documents\ASU": {
            "topics": ["chemistry", "coursework"],
            "file_count": 5
        },
    }
    graph_semantic.SEMANTIC_INDEX.write_text(
        json.dumps(index), encoding="utf-8"
    )
    result = graph_semantic.query("invoice.pdf", "billing statement")
    paths = [r[0] for r in result]
    assert r"C:\Users\xboxf\Documents\Finance" in paths


def test_query_returns_at_most_three(isolated_files):
    index = {
        rf"C:\Folder{i}": {"topics": ["invoice"], "file_count": i}
        for i in range(6)
    }
    graph_semantic.SEMANTIC_INDEX.write_text(
        json.dumps(index), encoding="utf-8"
    )
    result = graph_semantic.query("invoice.pdf", "")
    assert len(result) <= 3


def test_query_result_structure(isolated_files):
    index = {
        r"C:\Users\xboxf\Documents\Finance": {
            "topics": ["invoice", "finance"],
            "file_count": 3
        }
    }
    graph_semantic.SEMANTIC_INDEX.write_text(
        json.dumps(index), encoding="utf-8"
    )
    result = graph_semantic.query("invoice.pdf", "")
    assert all(
        isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], list)
        for r in result
    )


def test_refresh_scans_folders_and_builds_index(isolated_files):
    # Create a fake Documents tree in tmp_path
    docs = isolated_files / "Documents"
    finance = docs / "Finance"
    finance.mkdir(parents=True)
    (finance / "invoice_2026.pdf").touch()
    (finance / "billing_statement.pdf").touch()

    graph_semantic.refresh()

    assert graph_semantic.SEMANTIC_INDEX.exists()
    index = json.loads(
        graph_semantic.SEMANTIC_INDEX.read_text(encoding="utf-8")
    )
    finance_path = str(finance)
    assert finance_path in index
    assert "invoice" in index[finance_path]["topics"] or "billing" in index[finance_path]["topics"]
    assert index[finance_path]["file_count"] == 2


def test_refresh_leaves_index_untouched_on_error(isolated_files):
    existing = {r"C:\Users\xboxf\Documents\Old": {"topics": ["old"], "file_count": 1}}
    graph_semantic.SEMANTIC_INDEX.write_text(
        json.dumps(existing), encoding="utf-8"
    )
    # Point SCAN_ROOT at a path that will raise during os.walk
    with patch("graph_semantic.os.walk", side_effect=Exception("scan crashed")):
        graph_semantic.refresh()
    index = json.loads(
        graph_semantic.SEMANTIC_INDEX.read_text(encoding="utf-8")
    )
    assert r"C:\Users\xboxf\Documents\Old" in index
