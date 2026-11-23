#!/usr/bin/env python3
"""
doctor.py — Zero-dependency environment check & mirror-accelerated installer (k12-lesson-studio v5.0)

Usage:
  python doctor.py doctor              # Check Python packages, Node.js, Chrome/Edge, ffmpeg, LibreOffice
  python doctor.py setup [--mirror]    # Auto-install required Python packages (PyMuPDF, python-docx, python-pptx, Pillow)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import platform
import shutil
import subprocess
import sys

REQUIRED_PY = [
    ("fitz", "pymupdf"),
    ("docx", "python-docx"),
    ("pptx", "python-pptx"),
    ("PIL", "pillow"),
]

BROWSER_CANDS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_browser() -> str | None:
    for p in BROWSER_CANDS:
        if pathlib.Path(p).exists():
            return p
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("msedge")


def find_soffice() -> str | None:
    return (
        shutil.which("soffice")
        or (r"C:\Program Files\LibreOffice\program\soffice.com" if pathlib.Path(r"C:\Program Files\LibreOffice\program\soffice.com").exists() else None)
        or ("/Applications/LibreOffice.app/Contents/MacOS/soffice" if pathlib.Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").exists() else None)
    )


def run_doctor() -> dict:
    py_status = {}
    missing_py = []
    for mod, pkg in REQUIRED_PY:
        ok = importlib.util.find_spec(mod) is not None
        py_status[pkg] = ok
        if not ok:
            missing_py.append(pkg)

    node_bin = shutil.which("node")
    ffmpeg_bin = shutil.which("ffmpeg")
    browser_bin = find_browser()
    soffice_bin = find_soffice()

    report = {
        "ok": len(missing_py) == 0,
        "video_engine_ready": bool(node_bin and ffmpeg_bin and browser_bin),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "python_packages": py_status,
        "missing_python_packages": missing_py,
        "runtime_tools": {
            "node": node_bin,
            "ffmpeg": ffmpeg_bin,
            "browser": browser_bin,
            "libreoffice_optional": soffice_bin,
        },
    }
    return report


def run_setup(use_mirror: bool) -> int:
    pkgs = [pkg for _, pkg in REQUIRED_PY]
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]
    if use_mirror:
        cmd += ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn"]
    cmd += pkgs
    res = subprocess.run(cmd)
    if res.returncode != 0 and use_mirror:
        fallback = [sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs
        res = subprocess.run(fallback)
    rep = run_doctor()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["ok"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("doctor", help="Check runtime and Python package readiness")
    sp = sub.add_parser("setup", help="Install missing required Python packages")
    sp.add_argument("--mirror", action="store_true", help="Prefer Tsinghua PyPI mirror with official PyPI fallback")
    args = ap.parse_args()

    if args.cmd == "setup":
        return run_setup(args.mirror)
    rep = run_doctor()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
