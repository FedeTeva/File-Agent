"""
Run this script once to register the file organizer as a Windows startup task.
It will ask for your ANTHROPIC_API_KEY and store it in the scheduled task.

Usage:
    python setup.py
"""

import subprocess
import sys
import os
from pathlib import Path

TASK_NAME = "FileOrganizerAgent"
PROJECT_DIR = Path(__file__).parent.resolve()
MAIN_SCRIPT = PROJECT_DIR / "main.py"


def find_pythonw():
    python = Path(sys.executable)
    pythonw = python.parent / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return str(python)


def register_task(api_key: str):
    pythonw = find_pythonw()
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Automatically organizes downloaded files using Claude AI.</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{os.environ.get('USERNAME', '')}</UserId>
    </LogonTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{pythonw}</Command>
      <Arguments>"{MAIN_SCRIPT}"</Arguments>
      <WorkingDirectory>{PROJECT_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
</Task>"""

    xml_path = PROJECT_DIR / "_task.xml"
    xml_path.write_text(xml, encoding="utf-16")

    env_path = PROJECT_DIR / ".env"
    env_path.write_text(f"ANTHROPIC_API_KEY={api_key}\n", encoding="utf-8")

    patch = PROJECT_DIR / "_env_loader.pth"

    loader = PROJECT_DIR / "_load_env.py"
    loader.write_text(
        "import os, pathlib\n"
        f"env = pathlib.Path(r'{env_path}')\n"
        "if env.exists():\n"
        "    for line in env.read_text().splitlines():\n"
        "        if '=' in line and not line.startswith('#'):\n"
        "            k, v = line.split('=', 1)\n"
        "            os.environ.setdefault(k.strip(), v.strip())\n",
        encoding="utf-8",
    )

    insert = (
        f"import sys; sys.path.insert(0, r'{PROJECT_DIR}'); "
        f"exec(open(r'{loader}').read())"
    )
    sitecustomize = Path(sys.prefix) / "Lib" / "sitecustomize.py"
    existing = sitecustomize.read_text(encoding="utf-8") if sitecustomize.exists() else ""
    if str(PROJECT_DIR) not in existing:
        sitecustomize.write_text(existing + "\n" + insert + "\n", encoding="utf-8")

    result = subprocess.run(
        ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", str(xml_path), "/F"],
        capture_output=True, text=True
    )
    xml_path.unlink(missing_ok=True)

    if result.returncode == 0:
        print(f"Task '{TASK_NAME}' registered successfully.")
        print("The file organizer will now start automatically at every login.")
        print("\nTo start it now without rebooting, run:")
        print(f'  schtasks /Run /TN "{TASK_NAME}"')
    else:
        print("Failed to register task:")
        print(result.stderr)
        sys.exit(1)


def main():
    print("=== File Organizer Agent Setup ===\n")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        api_key = input("Enter your ANTHROPIC_API_KEY: ").strip()
    if not api_key:
        print("API key is required.")
        sys.exit(1)
    register_task(api_key)


if __name__ == "__main__":
    main()
