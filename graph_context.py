from pathlib import Path

import graph_behavior
import graph_semantic


def get_context(file_path: str) -> str:
    file_name = Path(file_path).name
    behavioral = graph_behavior.query(file_path)
    semantic = graph_semantic.query(file_name, "")
    sections: list[str] = []
    if behavioral:
        lines = ["Behavioral patterns (your confirmed past moves):"]
        for folder_path, score in behavioral:
            lines.append(f"  {folder_path} x{score}")
        sections.append("\n".join(lines))
    if semantic:
        lines = ["Semantic context (what lives in your folders):"]
        for folder_path, topics in semantic:
            lines.append(f"  {folder_path} — topics: {', '.join(topics)}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)
