#!/usr/bin/env python3
"""Audit a generated teaching PPTX for zero placeholders, editability, notes coverage, text overlap, embedded video, and bounds."""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import zipfile
from pptx import Presentation

PLACEHOLDER_RE = re.compile(r"\{\{|\}\}|\[插入|\[图片|\[此处|待补充|待填写|TODO|TBD|占位符|点击添加")
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".wmv", ".avi", ".webm"}


def audit(pptx_path: pathlib.Path) -> dict:
    prs = Presentation(str(pptx_path))
    slide_w = prs.slide_width.pt
    slide_h = prs.slide_height.pt

    videos = []
    with zipfile.ZipFile(pptx_path, "r") as zf:
        for info in zf.infolist():
            if info.filename.startswith("ppt/media/") and pathlib.Path(info.filename).suffix.lower() in VIDEO_EXTS:
                videos.append({"path": info.filename, "bytes": info.file_size})

    report = {
        "file": str(pptx_path),
        "slides": len(prs.slides),
        "slide_pt": [round(slide_w, 1), round(slide_h, 1)],
        "editable_text_shapes": 0,
        "native_tables": 0,
        "images": 0,
        "unique_images": 0,
        "duplicate_images": [],
        "videos": videos,
        "notes_present": 0,
        "missing_notes_slides": [],
        "placeholders": [],
        "out_of_bounds": [],
        "tiny_fonts": [],
        "text_overlaps": [],
        "passed": True,
    }

    image_hashes: dict[str, dict] = {}

    for idx, slide in enumerate(prs.slides, 1):
        text_boxes = []
        for sh in slide.shapes:
            left = sh.left.pt
            top = sh.top.pt
            right = left + sh.width.pt
            bottom = top + sh.height.pt
            if sh.has_text_frame:
                report["editable_text_shapes"] += 1
                txt = sh.text_frame.text.strip()
                if txt:
                    text_boxes.append((left, top, right, bottom, txt[:32]))
                if txt and PLACEHOLDER_RE.search(txt):
                    report["placeholders"].append({"slide": idx, "text": txt[:80]})
                if txt and (left < -4 or top < -4 or right > slide_w + 4 or bottom > slide_h + 4):
                    report["out_of_bounds"].append({
                        "slide": idx,
                        "text": txt[:40],
                        "box": [round(left, 1), round(top, 1), round(right, 1), round(bottom, 1)],
                    })
                for p in sh.text_frame.paragraphs:
                    for run in p.runs:
                        if run.text.strip() and run.font.size and run.font.size.pt < 10.5:
                            report["tiny_fonts"].append({"slide": idx, "pt": round(run.font.size.pt, 1), "text": run.text.strip()[:30]})
            if sh.has_table:
                report["native_tables"] += 1
            if sh.shape_type == 13:
                report["images"] += 1
                try:
                    blob = sh.image.blob
                    if len(blob) > 4096:
                        h = hashlib.sha256(blob).hexdigest()[:16]
                        entry = image_hashes.setdefault(h, {"sha256": h, "bytes": len(blob), "slides": []})
                        if idx not in entry["slides"]:
                            entry["slides"].append(idx)
                except Exception:
                    pass

        # Detect unintended overlapping non-empty text frames (skip nested background containers)
        for i in range(len(text_boxes)):
            a = text_boxes[i]
            for j in range(i + 1, len(text_boxes)):
                b = text_boxes[j]
                ow = min(a[2], b[2]) - max(a[0], b[0])
                oh = min(a[3], b[3]) - max(a[1], b[1])
                if ow > 8.0 and oh > 8.0:
                    area_a = max(1.0, (a[2] - a[0]) * (a[3] - a[1]))
                    area_b = max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
                    ov_area = ow * oh
                    if ov_area / min(area_a, area_b) > 0.18:
                        report["text_overlaps"].append({
                            "slide": idx,
                            "a": a[4],
                            "b": b[4],
                            "overlap_pt": [round(ow, 1), round(oh, 1)],
                        })

        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        if len(notes) >= 10:
            report["notes_present"] += 1
        else:
            report["missing_notes_slides"].append(idx)

    report["unique_images"] = len(image_hashes)
    report["duplicate_images"] = [v for v in image_hashes.values() if len(v["slides"]) > 1]

    if report["placeholders"] or report["missing_notes_slides"] or report["out_of_bounds"] or report["duplicate_images"]:
        report["passed"] = False
    return report


def render_contact_sheet(pptx_path: pathlib.Path, out_png: pathlib.Path) -> str | None:
    import math
    import shutil
    import subprocess
    import tempfile
    try:
        import fitz
        from PIL import Image, ImageDraw
    except Exception:
        return None
    soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.com"
    if not pathlib.Path(soffice).exists():
        return None
    with tempfile.TemporaryDirectory(prefix="ppt_audit_") as td:
        tdir = pathlib.Path(td)
        subprocess.run(
            [str(soffice), "--headless", "--convert-to", "pdf", "--outdir", str(tdir), str(pptx_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        pdf_path = tdir / (pptx_path.stem + ".pdf")
        if not pdf_path.exists():
            return None
        doc = fitz.open(str(pdf_path))
        n = len(doc)
        cols = 4 if n >= 9 else min(3, max(1, n))
        rows = math.ceil(n / cols)
        tw, th = 480, 270
        sheet = Image.new("RGB", (cols * tw, rows * th), (242, 238, 230))
        draw = ImageDraw.Draw(sheet)
        for i in range(n):
            pix = doc[i].get_pixmap(dpi=120)
            im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).resize((tw, th), Image.Resampling.LANCZOS)
            r, c = divmod(i, cols)
            sheet.paste(im, (c * tw, r * th))
            draw.rectangle([c * tw + 6, r * th + 6, c * tw + 64, r * th + 26], fill=(11, 26, 32))
            draw.text((c * tw + 14, r * th + 10), f"P{i + 1:02d}", fill=(247, 226, 184))
        doc.close()
        out_png.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(str(out_png), optimize=True)
        return str(out_png)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pptx", type=pathlib.Path)
    ap.add_argument("--allow-missing-notes", action="store_true", help="Allow single-slide style drafts without notes")
    ap.add_argument("--render-sheet", type=pathlib.Path, default=None, help="Optional PNG path for LibreOffice 1-shot visual contact sheet")
    args = ap.parse_args()

    res = audit(args.pptx)
    if args.render_sheet:
        sheet = render_contact_sheet(args.pptx, args.render_sheet)
        if sheet:
            res["contact_sheet"] = sheet
    if args.allow_missing_notes and not res["placeholders"] and not res["out_of_bounds"]:
        res["passed"] = True
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
