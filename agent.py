import os
import json
import mimetypes
from pathlib import Path
import anthropic
import graph_context

WATCH_ROOT = str(Path.home())
SKIP_DIRS = {"AppData", "$Recycle.Bin", ".git", "file_organizer"}

client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "get_file_info",
        "description": "Get metadata and a content preview of the downloaded file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "scan_directory",
        "description": "List subdirectories under a given path up to a max depth.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to scan"},
                "max_depth": {"type": "integer", "description": "Max depth to recurse (default 3)", "default": 3},
            },
            "required": ["path"],
        },
    },
    {
        "name": "propose_destination",
        "description": "Propose the best existing destination folder for the file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_path": {"type": "string", "description": "Full absolute path of the destination folder"},
                "reason": {"type": "string", "description": "One-sentence explanation for the choice"},
            },
            "required": ["destination_path", "reason"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are a file organizer assistant. When given a new downloaded file, you must:\n"
    "1. Call get_file_info to understand the file.\n"
    f"2. Call scan_directory starting at {WATCH_ROOT} to explore available folders.\n"
    "3. Choose the most logical EXISTING folder as the destination.\n"
    "4. Call propose_destination with the full destination folder path and a one-sentence reason.\n"
    "Do NOT propose creating new folders. Only use existing ones."
)


def _get_file_info(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}
    mime, _ = mimetypes.guess_type(path)
    info = {
        "name": p.name,
        "extension": p.suffix.lower(),
        "size_bytes": p.stat().st_size,
        "mime_type": mime or "unknown",
        "preview": None,
    }
    if mime and mime.startswith("text/"):
        try:
            info["preview"] = p.read_text(errors="replace")[:500]
        except Exception:
            pass
    return info


def _scan_directory(path: str, max_depth: int = 3, _current_depth: int = 0) -> list:
    result = []
    try:
        for entry in sorted(Path(path).iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") or entry.name in SKIP_DIRS:
                continue
            node = {"name": entry.name, "path": str(entry)}
            if _current_depth < max_depth - 1:
                children = _scan_directory(str(entry), max_depth, _current_depth + 1)
                if children:
                    node["children"] = children
            result.append(node)
    except PermissionError:
        pass
    return result


def _handle_tool(tool_name: str, tool_input: dict):
    if tool_name == "get_file_info":
        return _get_file_info(tool_input["path"])
    if tool_name == "scan_directory":
        depth = tool_input.get("max_depth", 3)
        return _scan_directory(tool_input["path"], depth)
    return {}


def run(file_path: str) -> tuple[str, str] | None:
    """Run the agent for a given file. Returns (destination_path, reason) or None."""
    past = graph_context.get_context(file_path)
    user_msg = f"A new file was downloaded: {file_path}\nPlease determine the best folder to move it to."
    if past:
        user_msg += f"\n\n{past}"
    messages = [{"role": "user", "content": user_msg}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            return None

        tool_results = []
        destination = None

        for tool_use in tool_uses:
            if tool_use.name == "propose_destination":
                destination = (tool_use.input["destination_path"], tool_use.input["reason"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": "Proposal recorded.",
                })
            else:
                result = _handle_tool(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        if destination:
            return destination

        if response.stop_reason == "end_turn":
            return None
