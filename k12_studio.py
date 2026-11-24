#!/usr/bin/env python3
"""
k12_studio.py — Unified Single-Entry CLI & Package Quality Auditor for K12 Lesson Studio (v5.1)

Subcommands:
  doctor          1-second environment & dependency diagnostic (pure stdlib)
  setup           Auto-install required Python packages with Tsinghua mirror fallback
  scan-pdf        Inspect textbook PDF metadata, TOC bookmarks, scanned-page ratio & keyword hits
  extract-pdf     Export chapter PDF excerpt (preserving TOC) + text + auto-rendered scanned pages
  docx            Convert Markdown to printable A4 Word (.docx) with teacher red-ink & student answer lines
  render-video    Render deterministic Three.js 3D MP4 + poster + 4x4 contact sheet (+ optional compact HTML MP4)
  build-html      Assemble single-file offline 3D classroom lab + 4-team PK HTML from theater_base.html
  audit-html      Headless browser verification + 4x4 contact sheet for interactive HTML
  audit-pptx      Structural & visual verification (0 duplicates, 0 overlaps, notes, video) for PPTX
  verify-exam     Validate 100-pt exam JSON & optionally export single-source Student/Teacher Markdown
  verify-grading  Validate batch grading records & single-source error tag ratios
  package-audit   Static self-audit of the Skill package (depth <= 2, < 3 MB, frontmatter, 0 missing refs)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import py_compile
import re
import shutil
import subprocess
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _run_py_script(script_name: str, extra_args: list[str]) -> int:
    cmd = [sys.executable, "-X", "utf8", str(SCRIPTS_DIR / script_name)] + extra_args
    return subprocess.run(cmd).returncode


def _run_node_script(script_name: str, extra_args: list[str]) -> int:
    node_bin = shutil.which("node")
    if not node_bin:
        print(json.dumps({"passed": False, "error": "node not found in PATH"}, ensure_ascii=False))
        return 1
    cmd = [node_bin, str(SCRIPTS_DIR / script_name)] + extra_args
    return subprocess.run(cmd).returncode


# Built-in static scanner to prevent WorkBuddy Open Platform "内置文件缺失" rejections!
ALLOWED_EXAMPLE_LITERALS = {
    "Three.js",
    "three.js",
    "Node.js",
    "node.js",
    "edge-tts==7.3.1",
    "node_modules",
}
FILE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_<>/\\:-])"
    r"([A-Za-z0-9_.\u4e00-\u9fff/-]+\.(?:py|mjs|js|json|html|md|svg|txt|css|mp4|png|webp|docx|pptx|pdf))"
    r"(?![A-Za-z0-9_>])"
)


def run_package_audit() -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    all_files = [
        p for p in SKILL_DIR.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc")
    ]
    rel_set = {p.relative_to(SKILL_DIR).as_posix() for p in all_files}
    basename_map: dict[str, list[str]] = {}
    for rel in rel_set:
        bn = pathlib.PurePosixPath(rel).name
        basename_map.setdefault(bn, []).append(rel)

    total_bytes = sum(p.stat().st_size for p in all_files)
    max_depth = max(len(p.relative_to(SKILL_DIR).parts) for p in all_files) if all_files else 0

    # 1. Directory depth <= 2 inside skill root (e.g. scripts/foo.py has 2 parts: ('scripts', 'foo.py'))
    if max_depth > 2:
        deep = [p.relative_to(SKILL_DIR).as_posix() for p in all_files if len(p.relative_to(SKILL_DIR).parts) > 2]
        errors.append(f"Directory depth exceeds 2 levels inside skill root: {deep}")

    # 2. Size < 3 MB hard limit
    if total_bytes >= 3 * 1024 * 1024:
        errors.append(f"Total unzipped size {total_bytes} bytes exceeds 3 MB limit")

    # 3. SKILL.md & workbuddy.json metadata parity check
    skill_md = SKILL_DIR / "SKILL.md"
    wb_json = SKILL_DIR / "workbuddy.json"
    if not skill_md.exists():
        errors.append("Missing SKILL.md")
    if not wb_json.exists():
        errors.append("Missing workbuddy.json")

    if skill_md.exists() and wb_json.exists():
        md_txt = skill_md.read_text(encoding="utf-8")
        wb_data = json.loads(wb_json.read_text(encoding="utf-8"))
        m_fm = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", md_txt, flags=re.S)
        if not m_fm:
            errors.append("SKILL.md missing valid YAML frontmatter block")
        else:
            fm = m_fm.group(1)
            for key in ("name:", "display_name:", "version:", "description:", "description_zh:"):
                if key not in fm:
                    errors.append(f"SKILL.md frontmatter missing key {key}")
            if f'"{wb_data.get("display_name", "")}"' not in fm:
                errors.append("display_name mismatch between SKILL.md and workbuddy.json")

    # 4. Syntax check all bundled .py and .mjs files
    for p in all_files:
        if p.suffix == ".py":
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as exc:
                errors.append(f"Python syntax error in {p.relative_to(SKILL_DIR).as_posix()}: {exc}")
        elif p.suffix == ".mjs":
            node_bin = shutil.which("node")
            if node_bin:
                chk = subprocess.run([node_bin, "--check", str(p)], capture_output=True, text=True)
                if chk.returncode != 0:
                    errors.append(f"Node syntax error in {p.relative_to(SKILL_DIR).as_posix()}: {chk.stderr.strip()}")

    # 5. Reference integrity check across SKILL.md and references/*.md
    md_docs = [p for p in all_files if p.suffix == ".md"]
    dangling_refs: list[dict] = []
    for doc_path in md_docs:
        doc_rel = doc_path.relative_to(SKILL_DIR).as_posix()
        txt = doc_path.read_text(encoding="utf-8")
        for line_no, line in enumerate(txt.splitlines(), 1):
            # Strip angle-bracket runtime placeholders like <work_dir>/exam_spec.json or <课题>_教案.docx
            cleaned = re.sub(r"<[^>\n]+>[A-Za-z0-9_.\u4e00-\u9fff/-]*", "", line)
            cleaned = re.sub(r"https?://\S+", "", cleaned)
            for m in FILE_TOKEN_RE.finditer(cleaned):
                tok = m.group(1).strip("./")
                if not tok or tok in ALLOWED_EXAMPLE_LITERALS:
                    continue
                # Skip wildcard/generic extension mentions like .docx / .pptx / *.pdf
                if tok.startswith(".") or "/" not in tok and tok.split(".")[0] in {"", "md", "docx", "pptx", "pdf", "html", "mp4", "png", "webp", "json", "js", "py"}:
                    continue
                # Normalize {skill_dir}/ prefix if present
                tok_norm = re.sub(r"^\{?skill_dir\}?/", "", tok)
                # Workspace deliverable deliverables in Chinese folders (01-教材/..., 02-教案/..., 05-课后测改补/...) are user outputs, not bundled scripts
                if tok_norm.startswith(("01-教材/", "02-教案/", "03-授课PPT/", "04-大屏互动HTML/", "05-课后测改补/", "演示视频/")):
                    continue
                if tok_norm in {"教材核验清单.md", "整章课时规划.md", "错题急救小卡与3级变式题.docx"}:
                    continue
                # Otherwise, any referenced .py / .mjs / .js / .json / .html / .md MUST exist in the bundle!
                if tok_norm in rel_set:
                    continue
                if tok_norm in basename_map:
                    continue
                dangling_refs.append({"doc": doc_rel, "line": line_no, "token": tok})

    if dangling_refs:
        for item in dangling_refs:
            errors.append(f"Unbundled file reference '{item['token']}' in {item['doc']}:L{item['line']}")

    return {
        "passed": len(errors) == 0,
        "skill_dir": str(SKILL_DIR),
        "file_count": len(all_files),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 3),
        "max_directory_depth": max_depth,
        "dangling_references": dangling_refs,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="1-second environment diagnostic")
    p_setup = sub.add_parser("setup", help="Auto-install missing Python packages")
    p_setup.add_argument("--mirror", action="store_true", help="Prefer Tsinghua PyPI mirror")

    p_scan = sub.add_parser("scan-pdf", help="Scan textbook PDF metadata, TOC, scanned status & keyword hits")
    p_scan.add_argument("pdf")
    p_scan.add_argument("--keyword", default="")
    p_scan.add_argument("--json", action="store_true")

    p_ext = sub.add_parser("extract-pdf", help="Extract chapter PDF, raw text, and auto-rendered scanned page images")
    p_ext.add_argument("pdf")
    p_ext.add_argument("--start", type=int, required=True)
    p_ext.add_argument("--end", type=int, required=True)
    p_ext.add_argument("--out-pdf", required=True)
    p_ext.add_argument("--out-txt", default="")
    p_ext.add_argument("--render-pages-dir", default="")

    p_docx = sub.add_parser("docx", help="Convert Markdown to A4 Word (.docx)")
    p_docx.add_argument("md")
    p_docx.add_argument("docx")
    p_docx.add_argument("--compact", action="store_true")
    p_docx.add_argument("--mode", choices=["default", "student", "teacher", "card"], default="default")

    p_vid = sub.add_parser("render-video", help="Render deterministic Three.js 3D MP4 video")
    p_vid.add_argument("--scene", required=True)
    p_vid.add_argument("--out", required=True)
    p_vid.add_argument("--poster", default="")
    p_vid.add_argument("--poster-sec", default="")
    p_vid.add_argument("--contact-sheet", default="")
    p_vid.add_argument("--compact-out", default="")

    p_html = sub.add_parser("build-html", help="Build single-file offline interactive HTML lab")
    p_html.add_argument("--config", required=True)
    p_html.add_argument("--scenes", required=True)
    p_html.add_argument("--out", required=True)
    p_html.add_argument("--video", default="")
    p_html.add_argument("--poster", default="")

    p_ah = sub.add_parser("audit-html", help="Audit offline HTML lab via headless browser")
    p_ah.add_argument("html")
    p_ah.add_argument("--shots-dir", default="")

    p_ap = sub.add_parser("audit-pptx", help="Audit generated PPTX for 0 duplicates, 0 overlaps, notes & video")
    p_ap.add_argument("pptx")
    p_ap.add_argument("--render-sheet", default="")
    p_ap.add_argument("--allow-missing-notes", action="store_true")

    p_ve = sub.add_parser("verify-exam", help="Validate 100-pt exam JSON & export Student/Teacher Markdown")
    p_ve.add_argument("json_path")
    p_ve.add_argument("--target-total", type=float, default=100.0)
    p_ve.add_argument("--export-student-md", default="")
    p_ve.add_argument("--export-teacher-md", default="")

    p_vg = sub.add_parser("verify-grading", help="Validate batch grading JSON & export single-source summary Markdown")
    p_vg.add_argument("json_path")
    p_vg.add_argument("--export-summary-md", default="")

    sub.add_parser("package-audit", help="Static self-audit of Skill package integrity & references")

    args = ap.parse_args()

    if args.cmd == "doctor":
        return _run_py_script("doctor.py", ["doctor"])
    if args.cmd == "setup":
        return _run_py_script("doctor.py", ["setup"] + (["--mirror"] if args.mirror else []))
    if args.cmd == "scan-pdf":
        ex = [args.pdf]
        if args.keyword:
            ex += ["--keyword", args.keyword]
        if args.json:
            ex += ["--json"]
        return _run_py_script("extract_textbook.py", ex)
    if args.cmd == "extract-pdf":
        ex = [args.pdf, "--start", str(args.start), "--end", str(args.end), "--out-pdf", args.out_pdf]
        if args.out_txt:
            ex += ["--out-txt", args.out_txt]
        if args.render_pages_dir:
            ex += ["--render-pages-dir", args.render_pages_dir]
        return _run_py_script("extract_textbook.py", ex)
    if args.cmd == "docx":
        ex = [args.md, args.docx, "--mode", args.mode]
        if args.compact:
            ex.append("--compact")
        return _run_py_script("md_to_docx.py", ex)
    if args.cmd == "render-video":
        ex = ["--scene", args.scene, "--out", args.out]
        if args.poster:
            ex += ["--poster", args.poster]
        if args.poster_sec:
            ex += ["--poster-sec", str(args.poster_sec)]
        if args.contact_sheet:
            ex += ["--contact-sheet", args.contact_sheet]
        if args.compact_out:
            ex += ["--compact-out", args.compact_out]
        return _run_node_script("render_video.mjs", ex)
    if args.cmd == "build-html":
        ex = ["--config", args.config, "--scenes", args.scenes, "--out", args.out]
        if args.video:
            ex += ["--video", args.video]
        if args.poster:
            ex += ["--poster", args.poster]
        return _run_py_script("build_html.py", ex)
    if args.cmd == "audit-html":
        ex = [args.html] + ([args.shots_dir] if args.shots_dir else [])
        return _run_node_script("audit_html.mjs", ex)
    if args.cmd == "audit-pptx":
        ex = [args.pptx]
        if args.render_sheet:
            ex += ["--render-sheet", args.render_sheet]
        if args.allow_missing_notes:
            ex.append("--allow-missing-notes")
        return _run_py_script("audit_pptx.py", ex)
    if args.cmd == "verify-exam":
        ex = ["exam", args.json_path, "--target-total", str(args.target_total)]
        if args.export_student_md:
            ex += ["--export-student-md", args.export_student_md]
        if args.export_teacher_md:
            ex += ["--export-teacher-md", args.export_teacher_md]
        return _run_py_script("verify_exam.py", ex)
    if args.cmd == "verify-grading":
        ex = ["grading", args.json_path]
        if args.export_summary_md:
            ex += ["--export-summary-md", args.export_summary_md]
        return _run_py_script("verify_exam.py", ex)
    if args.cmd == "package-audit":
        rep = run_package_audit()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if rep["passed"] else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
