# File Organizer Agent

A Windows Downloads organizer powered by Claude. A tool use agent reads each new file, scans your existing folders, and proposes a destination that you approve in a popup. Two knowledge graphs sharpen its picks over time: a networkx graph that learns from every move you confirm, and a nightly keyword index of what lives in your Documents folders.

## How it works

1. **Watch.** `watcher.py` monitors your Downloads folder. It skips partial downloads (`.crdownload`, `.part`, `.tmp`, `.download`) and waits until the file size stops changing.
2. **Gather context.** `graph_context.py` asks both graphs for hints:
   * **Behavioral graph** (`graph_behavior.py`): which folders you have sent similar files to before, matched on extension plus filename keywords. Recent moves count more (scores decay by 10% per day, capped at 90 days).
   * **Semantic index** (`graph_semantic.py`): which folders in Documents contain files whose names share keywords with the new file.
3. **Decide.** `agent.py` runs Claude (Sonnet) with three tools: `get_file_info` (name, extension, size, MIME type, text preview), `scan_directory` (your existing folder tree), and `propose_destination`. It only proposes folders that already exist.
4. **Confirm.** `notifier.py` shows a popup with the suggestion and a one sentence reason. Choose **Move**, **Choose Folder**, or **Skip**. Name collisions get a numbered suffix like `report (1).pdf`.
5. **Learn.** Every confirmed move is written to the behavioral graph immediately. The semantic index rebuilds every night at 02:00.

```
Downloads ─► watcher.py ─► agent.py ◄─ graph_context.py ◄─┬─ graph_behavior.py (per move)
                              │                            └─ graph_semantic.py (nightly)
                          notifier.py ─► confirmed move ─► graph_behavior.record()
```

## Requirements

* Windows 10 or 11
* Python 3.10 or newer (developed on 3.14)
* An Anthropic API key

## Setup

1. Install dependencies:

   ```
   py -m pip install -r requirements.txt
   ```

2. **Update the hard coded paths** to match your user folder:

   | File | Constant | Default |
   |---|---|---|
   | `agent.py` | `WATCH_ROOT` | `C:\Users\xboxf` |
   | `watcher.py` | `DOWNLOADS` | `C:\Users\xboxf\Downloads` |
   | `graph_semantic.py` | `SCAN_ROOT` | `C:\Users\xboxf\Documents` |

3. Register it to start at logon:

   ```
   py setup.py
   ```

   This asks for your API key (or reads `ANTHROPIC_API_KEY`), saves it to `.env`, and creates a Task Scheduler task named `FileOrganizerAgent` that runs `main.py` silently with `pythonw`.

4. Start it now without rebooting:

   ```
   schtasks /Run /TN "FileOrganizerAgent"
   ```

To run it in a terminal instead (useful for debugging), set `ANTHROPIC_API_KEY` and run `py main.py`. Stop it with Ctrl+C.

> On some systems `python` opens the Microsoft Store instead of Python. Use the `py` launcher as shown above.

## Files

| File | Purpose |
|---|---|
| `main.py` | Entry point. Starts the watcher and the nightly scheduler. |
| `watcher.py` | Watches Downloads and hands finished files to the agent. |
| `agent.py` | Claude tool use loop that proposes a destination. |
| `notifier.py` | Approval popup, file move, and behavioral graph update. |
| `graph_behavior.py` | networkx graph of your confirmed moves. |
| `graph_semantic.py` | Nightly keyword index of your Documents folders. |
| `graph_context.py` | Combines both graphs into prompt context. |
| `_keywords.py` | Shared filename tokenizer with stopword filtering. |
| `setup.py` | Registers the logon task and stores the API key. |

Created at runtime and kept out of git: `.env`, `organizer.log`, `behavior_graph.json`, `semantic_index.json`.

## Tests

```
py -m pytest tests
```

## Uninstall

```
schtasks /Delete /TN "FileOrganizerAgent" /F
```

`setup.py` also appends a line to `sitecustomize.py` in your Python install's `Lib` folder so the API key loads automatically. Remove that line if you uninstall.

## Notes

* Files never move without your approval.
* The agent is instructed to propose only existing folders, and you see the full path before anything moves.
* An older `move_history.json` from earlier versions is migrated into the behavioral graph on first run.
