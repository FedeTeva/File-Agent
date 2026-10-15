import json
import logging
import os
from pathlib import Path

from _keywords import extract_keywords

SEMANTIC_INDEX = Path(__file__).parent / "semantic_index.json"
SCAN_ROOT = str(Path.home() / "Documents")
MAX_DEPTH = 3


def _build_index(scan_root: str) -> dict:
    index: dict[str, dict] = {}
    root_path = Path(scan_root)
    for dirpath, dirnames, filenames in os.walk(scan_root):
        depth = len(Path(dirpath).relative_to(root_path).parts)
        if depth >= MAX_DEPTH:
            dirnames.clear()
            continue
        topics: set[str] = set()
        folder_name = Path(dirpath).name
        topics.update(extract_keywords(folder_name))
        for fname in filenames:
            topics.update(extract_keywords(Path(fname).stem))
        if topics:
            index[dirpath] = {
                "topics": sorted(topics),
                "file_count": len(filenames),
            }
    return index


def refresh() -> None:
    try:
        index = _build_index(SCAN_ROOT)
        payload = json.dumps(index, indent=2)
        tmp = SEMANTIC_INDEX.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, SEMANTIC_INDEX)
    except Exception as e:
        logging.error(f"Semantic index refresh failed: {e}")


def _load_index() -> dict:
    if not SEMANTIC_INDEX.exists():
        return {}
    try:
        return json.loads(SEMANTIC_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return {}


def query(file_name: str, content_preview: str) -> list[tuple[str, list[str]]]:
    index = _load_index()
    if not index:
        return []
    keywords = set(extract_keywords(f"{Path(file_name).stem} {content_preview}"))
    results: list[tuple[str, list[str], float]] = []
    for folder_path, data in index.items():
        topics = data.get("topics", [])
        if not topics:
            continue
        overlap = len(keywords & set(t.lower() for t in topics))
        if overlap > 0:
            score = overlap / len(topics)
            results.append((folder_path, topics, score))
    results.sort(key=lambda x: -x[2])
    return [(path, topics) for path, topics, _ in results[:3]]
