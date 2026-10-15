import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import graph_behavior


def confirm_and_move(file_path: str, destination: str, reason: str) -> bool:
    """Show a popup dialog and move the file if the user approves. Returns True if moved."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    result = {"action": None, "path": destination}

    dialog = tk.Toplevel(root)
    dialog.title("File Organizer")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)

    file_name = Path(file_path).name

    tk.Label(dialog, text="New file downloaded:", font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=16, pady=(16, 0))
    tk.Label(dialog, text=file_name, font=("Segoe UI", 9), anchor="w", wraplength=420).pack(fill="x", padx=16)

    tk.Label(dialog, text="Suggested destination:", font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=16, pady=(12, 0))
    tk.Label(dialog, text=destination, font=("Segoe UI", 9), anchor="w", wraplength=420, fg="#0066cc").pack(fill="x", padx=16)

    tk.Label(dialog, text="Reason:", font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=16, pady=(12, 0))
    tk.Label(dialog, text=reason, font=("Segoe UI", 9), anchor="w", wraplength=420).pack(fill="x", padx=16)

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=16, padx=16, fill="x")

    def on_move():
        result["action"] = "move"
        dialog.destroy()

    def on_skip():
        result["action"] = "skip"
        dialog.destroy()

    def on_choose():
        chosen = filedialog.askdirectory(title="Choose destination folder", initialdir=destination)
        if chosen:
            result["path"] = chosen
            result["action"] = "move"
            dialog.destroy()

    tk.Button(btn_frame, text="Move", width=10, bg="#0066cc", fg="white", font=("Segoe UI", 9, "bold"), command=on_move).pack(side="left", padx=(0, 8))
    tk.Button(btn_frame, text="Choose Folder", width=14, command=on_choose).pack(side="left", padx=(0, 8))
    tk.Button(btn_frame, text="Skip", width=10, command=on_skip).pack(side="left")

    dialog.update_idletasks()
    w, h = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
    sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
    dialog.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    root.wait_window(dialog)
    root.destroy()

    if result["action"] == "move":
        dest_dir = Path(result["path"])
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / Path(file_path).name
        if dest_file.exists():
            base = dest_file.stem
            ext = dest_file.suffix
            i = 1
            while dest_file.exists():
                dest_file = dest_dir / f"{base} ({i}){ext}"
                i += 1
        shutil.move(file_path, dest_file)
        graph_behavior.record(file_path, str(dest_dir))
        return True

    return False
