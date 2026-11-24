#!/usr/bin/env python3
"""
build_html.py — Assemble a verified, 100% offline K12 interactive big-screen HTML lab
from the bundled theater_base.html shell + subject config.json + subject scenes.js
(+ optional offline base64 MP4 demonstration video & poster frame).

Usage:
  py -X utf8 build_html.py --config config.json --scenes scenes.js --out lab.html [--video demo.mp4 --poster poster.png]
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import re
import sys


def b64_data_uri(file_path: pathlib.Path, mime: str) -> str:
    raw = file_path.read_bytes()
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def validate_config(cfg: dict) -> None:
    required = ["title", "brandTitle", "brandSub", "brandTag", "films", "teams", "questions"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"config.json missing required keys: {missing}")
    if len(cfg["films"]) < 1:
        raise ValueError("config.json must define at least 1 film scene")
    for f_idx, fm in enumerate(cfg["films"], 1):
        fm.setdefault("num", f"{f_idx:02d}")
        if not fm.get("name"):
            pill = str(fm.get("pill", "")).strip()
            fm["name"] = re.sub(r"^\d+[\s.·、-]*", "", pill).strip() if pill else str(fm.get("title", f"分镜{f_idx}"))[:8]
    if len(cfg["teams"]) != 4:
        raise ValueError(f"config.json must define exactly 4 teams, got {len(cfg['teams'])}")
    for t_idx, tm in enumerate(cfg["teams"], 1):
        if not tm.get("name"):
            raise ValueError(f"Team {t_idx} missing 'name'")
        if not (tm.get("color") or tm.get("c")):
            raise ValueError(f"Team {t_idx} must specify hex 'color' (e.g. '#38BDF8')")
        tm.setdefault("color", tm.get("c"))
        tm.setdefault("short", tm.get("tag") or tm["name"])
    if len(cfg["questions"]) < 4:
        raise ValueError(f"config.json must define at least 4 PK questions, got {len(cfg['questions'])}")
    for idx, q in enumerate(cfg["questions"], 1):
        if not (0 <= q["a"] < len(q["opts"])):
            raise ValueError(f"Question {idx} has invalid answer index a={q['a']}")
        if q.get("answerText") and q["answerText"] not in q["opts"][q["a"]] and q["opts"][q["a"]] not in q["answerText"]:
            raise ValueError(
                f"Question {idx} answerText ({q['answerText']!r}) does not match opts[{q['a']}] ({q['opts'][q['a']]!r})"
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=pathlib.Path, required=True)
    ap.add_argument("--scenes", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--video", type=pathlib.Path, default=None)
    ap.add_argument("--poster", type=pathlib.Path, default=None)
    ap.add_argument("--shell", type=pathlib.Path, default=None)
    args = ap.parse_args()

    skill_root = pathlib.Path(__file__).resolve().parent.parent
    shell_path = args.shell or (skill_root / "assets" / "theater_base.html")
    if not shell_path.exists():
        raise FileNotFoundError(f"Theater shell not found: {shell_path}")

    cfg = json.loads(args.config.read_text(encoding="utf-8-sig"))
    validate_config(cfg)

    scenes_js = args.scenes.read_text(encoding="utf-8-sig")
    html = shell_path.read_text(encoding="utf-8")

    video_uri = b64_data_uri(args.video, "video/mp4") if args.video and args.video.exists() else ""
    poster_uri = b64_data_uri(args.poster, "image/png") if args.poster and args.poster.exists() else ""

    cfg_json = json.dumps(cfg, ensure_ascii=False).replace("</script>", "<\\/script>")
    scenes_safe = scenes_js.replace("</script>", "<\\/script>")

    replacements = {
        "__PAGE_TITLE__": str(cfg["title"]),
        "__BRAND_TITLE__": str(cfg["brandTitle"]),
        "__BRAND_SUB__": str(cfg["brandSub"]),
        "__BRAND_TAG__": str(cfg["brandTag"]),
        "__VIDEO_POSTER__": poster_uri,
        "__VIDEO_SRC__": video_uri,
        "__VIDEO_CAPTION__": str(cfg.get("videoCaption", "3D 代码演示 · 离线直放")),
        "__CONFIG_JSON__": cfg_json,
        "__SCENES_JS__": scenes_safe,
    }
    for k, v in replacements.items():
        if k not in html:
            raise ValueError(f"Placeholder {k} missing in {shell_path}")
        html = html.replace(k, v)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Built offline HTML theater: {args.out} ({args.out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
