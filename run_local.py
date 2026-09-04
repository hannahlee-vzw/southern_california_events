"""
Local dev runner — use instead of `python main.py` on this machine.

The playwright chromium download is blocked by the corporate SSL proxy.
This script creates the expected browser path (once) then runs main.py.

Usage:  python run_local.py
"""
import os
import pathlib
import shutil
import sys

_CHROMIUM_SRC = (
    r"C:\Users\leeha8h\AppData\Local\ms-playwright"
    r"\chromium-1223\chrome-win64\chrome.exe"
)
_HEADLESS_SHELL_EXE = (
    r"C:\Users\leeha8h\AppData\Local\ms-playwright"
    r"\chromium_headless_shell-1234\chrome-headless-shell-win64"
    r"\chrome-headless-shell.exe"
)

dest = pathlib.Path(_HEADLESS_SHELL_EXE)
if not dest.exists():
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_CHROMIUM_SRC, dest)
    print(f"Created headless shell shim at {dest}")

import main

sys.exit(main.main())
