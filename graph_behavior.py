import json
import re
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from _keywords import extract_keywords

GRAPH_FILE = Path(__file__).parent / "behavior_graph.json"
OLD_HISTORY = Path(__file__).parent / "move_history.json"


def _save(g: nx.DiGraph) -> None:
    data = {
        "nodes": [{"id": n, **attrs} for n, attrs in g.nodes(data=True)],
        "edges": [
            {"src": u, "dst": v, **attrs}
            for u, v, attrs in g.edges(data=True)
        ],
    }
    GRAPH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load() -> nx.DiGraph:
    if not GRAPH_FILE.exists():
        return nx.DiGraph()
    raw = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    g = nx.DiGraph()
    for node in raw.get("nodes", []):
        nid = node["id"]
        g.add_node(nid, **{k: v for k, v in node.items() if k != "id"})
    for edge in raw.get("edges", []):
        g.add_edge(
            edge["src"],
            edge["dst"],
            **{k: v for k, v in edge.items() if k not in ("src", "dst")},
        )
    return g


def _migrate() -> None:
    if not OLD_HISTORY.exists():
        return
    data = json.loads(OLD_HISTORY.read_text(encoding="utf-8"))
    g = _load()
    now = datetime.now(timezone.utc).isoformat()
    for ext, destinations in data.items():
        ctx_id = f"ctx:ext:{ext}"
        if not g.has_node(ctx_id):
            g.add_node(ctx_id, type="context", pattern=f"ext:{ext}")
        for dest, count in destinations.items():
            folder_id = f"folder:{dest}"
            if not g.has_node(folder_id):
                g.add_node(folder_id, type="folder", path=dest)
            if g.has_edge(ctx_id, folder_id):
                g[ctx_id][folder_id]["weight"] += count
            else:
                g.add_edge(ctx_id, folder_id, weight=count, last_seen=now)
    _save(g)
    OLD_HISTORY.unlink()


# Migrate old history only if no behavioral graph exists yet
if not GRAPH_FILE.exists():
    _migrate()


def record(file_path: str, destination: str) -> None:
    g = _load()
    stem = Path(file_path).stem
    ext = Path(file_path).suffix.lower() or ".unknown"
    keywords = extract_keywords(stem)
    folder_id = f"folder:{destination}"
    if not g.has_node(folder_id):
        g.add_node(folder_id, type="folder", path=destination)
    now = datetime.now(timezone.utc).isoformat()
    patterns = [f"ext:{ext}"] + [f"ext:{ext}+kw:{kw}" for kw in keywords]
    for pattern in patterns:
        ctx_id = f"ctx:{pattern}"
        if not g.has_node(ctx_id):
            g.add_node(ctx_id, type="context", pattern=pattern)
        if g.has_edge(ctx_id, folder_id):
            g[ctx_id][folder_id]["weight"] += 1
            g[ctx_id][folder_id]["last_seen"] = now
        else:
            g.add_edge(ctx_id, folder_id, weight=1, last_seen=now)
    _save(g)


def query(file_path: str) -> list[tuple[str, int]]:
    g = _load()
    if g.number_of_nodes() == 0:
        return []
    stem = Path(file_path).stem
    ext = Path(file_path).suffix.lower() or ".unknown"
    keywords = extract_keywords(stem)
    patterns = [f"ctx:ext:{ext}"] + [f"ctx:ext:{ext}+kw:{kw}" for kw in keywords]
    now = datetime.now(timezone.utc)
    scores: dict[str, float] = {}
    for ctx_id in patterns:
        if not g.has_node(ctx_id):
            continue
        for _, folder_id, data in g.out_edges(ctx_id, data=True):
            last_seen = datetime.fromisoformat(data["last_seen"])
            days = min((now - last_seen).days, 90)
            score = data["weight"] * (0.9 ** days)
            scores[folder_id] = scores.get(folder_id, 0.0) + score
    top3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
    return [(g.nodes[fid]["path"], round(sc)) for fid, sc in top3]
