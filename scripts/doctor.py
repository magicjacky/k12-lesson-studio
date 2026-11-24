#!/usr/bin/env python3
"""
doctor.py — Zero-dependency environment check & mirror-accelerated installer (k12-lesson-studio v5.1)

Usage:
  python doctor.py doctor              # Check Python packages, Node.js, Chrome/Edge, ffmpeg, LibreOffice
  python doctor.py setup [--mirror]    # Auto-install required Python packages (PyMuPDF, python-docx, python-pptx, Pillow)
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import pathlib
import platform
import shutil
import subprocess
import sys

REQUIRED_PY = [
    ("fitz", "pymupdf", "PyMuPDF"),
    ("docx", "python-docx", "python-docx"),
    ("pptx", "python-pptx", "python-pptx"),
    ("PIL", "pillow", "pillow"),
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
    "/usr/bin/chromium-browser",
]


def find_browser() -> str | None:
    for p in BROWSER_CANDS:
        if pathlib.Path(p).exists():
            return p
    return (
        shutil.which("google-chrome")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("msedge")
    )


def find_soffice() -> str | None:
    return (
        shutil.which("soffice")
        or (r"C:\Program Files\LibreOffice\program\soffice.com" if pathlib.Path(r"C:\Program Files\LibreOffice\program\soffice.com").exists() else None)
        or ("/Applications/LibreOffice.app/Contents/MacOS/soffice" if pathlib.Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").exists() else None)
    )


def run_doctor() -> dict:
    py_ok = sys.version_info >= (3, 10)
    py_status = {}
    missing_py = []
    for mod, pip_name, dist_name in REQUIRED_PY:
        found = importlib.util.find_spec(mod) is not None
        ver = None
        if found:
            try:
                ver = importlib.metadata.version(dist_name)
            except Exception:
                ver = "installed"
        py_status[pip_name] = {"ok": found, "version": ver}
        if not found:
            missing_py.append(pip_name)

    node_bin = shutil.which("node")
    ffmpeg_bin = shutil.which("ffmpeg")
    browser_bin = find_browser()
    soffice_bin = find_soffice()

    hints = []
    if not py_ok:
        hints.append("需要 Python 3.10 及以上版本。")
    if missing_py:
        skill_root = pathlib.Path(__file__).resolve().parent.parent
        hints.append(f'自动补齐 Python 依赖：python "{skill_root / "k12_studio.py"}" setup --mirror')
    if not (node_bin and ffmpeg_bin and browser_bin):
        hints.append("3D 代码视频渲染需要本机已安装 Node.js、ffmpeg 与 Chrome/Edge 浏览器。")

    return {
        "engine": "K12 Lesson Studio v5.1",
        "ok": py_ok and len(missing_py) == 0,
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
        "hints": hints,
    }


def run_setup(use_mirror: bool) -> int:
    pkgs = [pip_name for _, pip_name, _ in REQUIRED_PY]
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]
    if use_mirror:
        cmd += ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn"]
    cmd += pkgs
    res = subprocess.run(cmd)
    if res.returncode != 0 and use_mirror:
        fallback = [sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs
        subprocess.run(fallback)
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
