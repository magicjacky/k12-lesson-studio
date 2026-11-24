#!/usr/bin/env python3
"""
extract_textbook.py — Textbook PDF Metadata/TOC Scanner, Chapter Excerpt Exporter & Scanned-Page Renderer (v5.1)

Capabilities:
1. Scan front copyright pages + back colophon/postscript pages + embedded PDF TOC bookmarks.
2. Detect electronic text vs scanned image-only pages automatically.
3. Export lossless chapter excerpt PDF while preserving shifted TOC bookmarks.
4. Auto-render scanned/low-text pages (or all chapter pages via --render-pages-dir) to PNG + 4-column contact sheet.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import fitz


def _clean_lines(txt: str) -> list[str]:
    return [ln.strip() for ln in txt.splitlines() if ln.strip()]


def scan_pdf(pdf_path: pathlib.Path, keyword: str = "", as_json: bool = False) -> dict:
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    toc_raw = doc.get_toc() or []
    toc_items = [{"level": lv, "title": title.strip(), "page": pg} for lv, title, pg in toc_raw[:80]]

    # Sample pages to detect scanned PDFs
    sample_indices = sorted(set(list(range(min(10, total))) + list(range(0, total, max(1, total // 15)))))
    low_text_sample = 0
    for idx in sample_indices:
        if len("".join(doc[idx].get_text().split())) < 25:
            low_text_sample += 1
    scanned_ratio = round(low_text_sample / max(1, len(sample_indices)), 2)
    is_likely_scanned = scanned_ratio >= 0.65

    front_pages = []
    for i in range(min(8, total)):
        lines = _clean_lines(doc[i].get_text())
        front_pages.append({"page": i + 1, "preview": " | ".join(lines[:6])[:180]})

    back_pages = []
    for i in range(max(8, total - 3), total):
        lines = _clean_lines(doc[i].get_text())
        if lines:
            back_pages.append({"page": i + 1, "preview": " | ".join(lines[:6])[:180]})

    keyword_hits = []
    if keyword:
        for lv, title, pg in toc_raw:
            if keyword in title:
                keyword_hits.append({"source": "toc", "page": pg, "preview": f"[L{lv}] {title.strip()}"})
        for i in range(total):
            txt = doc[i].get_text()
            if keyword in txt:
                lines = _clean_lines(txt)
                keyword_hits.append({"source": "page_text", "page": i + 1, "preview": " | ".join(lines[:5])[:180]})

    rep = {
        "file": pdf_path.name,
        "total_pages": total,
        "metadata": {k: v for k, v in (doc.metadata or {}).items() if v},
        "toc_count": len(toc_raw),
        "toc": toc_items,
        "scanned_page_ratio_est": scanned_ratio,
        "is_likely_scanned": is_likely_scanned,
        "front_pages": front_pages,
        "back_pages": back_pages,
        "keyword": keyword,
        "keyword_hits": keyword_hits[:60],
    }
    doc.close()

    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return rep

    print(f"File: {rep['file']} | Total pages: {total} | Scanned est: {scanned_ratio * 100:.0f}% ({'SCANNED' if is_likely_scanned else 'ELECTRONIC'})")
    if toc_items:
        print(f"\n--- Embedded TOC Bookmarks ({len(toc_raw)} total, showing up to 30) ---")
        for item in toc_items[:30]:
            indent = "  " * max(0, item["level"] - 1)
            print(f"{indent}P{item['page']:03d}: {item['title']}")
    print("\n--- Front pages (1..8) ---")
    for fp in front_pages:
        print(f"PDF P{fp['page']:02d}: {fp['preview'] or '[image/blank page]'}")
    if back_pages:
        print("\n--- Back colophon pages ---")
        for bp in back_pages:
            print(f"PDF P{bp['page']:03d}: {bp['preview']}")
    if keyword:
        print(f"\n--- Keyword hits for '{keyword}' ({len(keyword_hits)}) ---")
        for hit in keyword_hits[:40]:
            print(f"PDF P{hit['page']:03d} ({hit['source']}): {hit['preview']}")
    return rep


def _build_contact_sheet(image_paths: list[tuple[int, pathlib.Path]], out_sheet: pathlib.Path) -> str | None:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    if not image_paths:
        return None
    cols = min(4, len(image_paths))
    rows = math.ceil(len(image_paths) / cols)
    tw, th = 380, 520
    sheet = Image.new("RGB", (cols * tw, rows * th), (244, 241, 234))
    draw = ImageDraw.Draw(sheet)
    for idx, (pg_no, img_p) in enumerate(image_paths[:24]):
        with Image.open(img_p) as im:
            im_rgb = im.convert("RGB")
            im_rgb.thumbnail((tw - 12, th - 36), Image.Resampling.LANCZOS)
            r, c = divmod(idx, cols)
            ox = c * tw + (tw - im_rgb.width) // 2
            oy = r * th + 30 + (th - 36 - im_rgb.height) // 2
            sheet.paste(im_rgb, (ox, oy))
            draw.rectangle([c * tw + 6, r * th + 4, c * tw + 108, r * th + 26], fill=(20, 38, 43))
            draw.text((c * tw + 14, r * th + 8), f"PDF P{pg_no:03d}", fill=(247, 226, 184))
    out_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(out_sheet), optimize=True)
    return str(out_sheet)


def extract_range(
    pdf_path: pathlib.Path,
    start_page: int,
    end_page: int,
    out_pdf: pathlib.Path,
    out_txt: pathlib.Path | None = None,
    render_pages_dir: pathlib.Path | None = None,
) -> dict:
    doc = fitz.open(str(pdf_path))
    s = max(0, start_page - 1)
    e = min(len(doc) - 1, end_page - 1)
    if e < s:
        s, e = e, s

    excerpt = fitz.open()
    excerpt.insert_pdf(doc, from_page=s, to_page=e)

    # Preserve shifted TOC bookmarks inside the chapter range
    toc_sub = []
    for lv, title, pg in (doc.get_toc() or []):
        if (s + 1) <= pg <= (e + 1):
            toc_sub.append([lv, title, pg - s])
    if toc_sub:
        # Normalize first bookmark level to 1 as required by MuPDF set_toc
        min_lv = min(item[0] for item in toc_sub)
        if min_lv > 1:
            toc_sub = [[item[0] - min_lv + 1, item[1], item[2]] for item in toc_sub]
        elif toc_sub[0][0] > 1:
            toc_sub[0][0] = 1
        try:
            excerpt.set_toc(toc_sub)
        except Exception:
            pass

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    excerpt.save(str(out_pdf))
    excerpt.close()

    scanned_pages: list[int] = []
    text_parts: list[str] = []
    for idx in range(s, e + 1):
        txt = doc[idx].get_text()
        char_cnt = len("".join(txt.split()))
        is_scan = char_cnt < 25
        if is_scan:
            scanned_pages.append(idx + 1)
        tag = "[SCANNED_OR_IMAGE_PAGE]" if is_scan else f"[ELECTRONIC_TEXT chars={char_cnt}]"
        text_parts.append(f"===== PDF Page {idx + 1} {tag} =====\n{txt}\n")

    if out_txt:
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text("\n".join(text_parts), encoding="utf-8")

    # Auto-render pages if explicitly requested OR if scanned pages are detected alongside --out-txt
    target_img_dir = render_pages_dir
    if target_img_dir is None and scanned_pages and out_txt is not None:
        target_img_dir = out_txt.parent / "scanned_pages"

    rendered_files: list[tuple[int, pathlib.Path]] = []
    contact_sheet_path = None
    if target_img_dir is not None:
        target_img_dir.mkdir(parents=True, exist_ok=True)
        pages_to_render = list(range(s + 1, e + 2)) if render_pages_dir is not None else scanned_pages
        for pg_no in pages_to_render:
            pix = doc[pg_no - 1].get_pixmap(dpi=150)
            img_p = target_img_dir / f"page_{pg_no:03d}.png"
            pix.save(str(img_p))
            rendered_files.append((pg_no, img_p))
        if rendered_files:
            contact_sheet_path = _build_contact_sheet(rendered_files, target_img_dir / "pages_contact_sheet.png")

    doc.close()

    res = {
        "saved_pdf": str(out_pdf),
        "pages": e - s + 1,
        "range": [s + 1, e + 1],
        "bytes": out_pdf.stat().st_size,
        "preserved_bookmarks": len(toc_sub),
        "scanned_pages_detected": scanned_pages,
        "saved_txt": str(out_txt) if out_txt else None,
        "rendered_pages_count": len(rendered_files),
        "pages_contact_sheet": contact_sheet_path,
    }
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=pathlib.Path, help="Path to textbook PDF")
    ap.add_argument("--keyword", default="", help="Keyword to search in TOC and pages")
    ap.add_argument("--json", action="store_true", help="Output scan report as JSON")
    ap.add_argument("--start", type=int, help="1-based start PDF page to extract")
    ap.add_argument("--end", type=int, help="1-based end PDF page to extract")
    ap.add_argument("--out-pdf", type=pathlib.Path, help="Output excerpt PDF path")
    ap.add_argument("--out-txt", type=pathlib.Path, default=None, help="Optional raw text dump path")
    ap.add_argument("--render-pages-dir", type=pathlib.Path, default=None, help="Directory to render page PNGs + contact sheet")
    args = ap.parse_args()

    if args.start and args.end and args.out_pdf:
        extract_range(args.pdf, args.start, args.end, args.out_pdf, args.out_txt, args.render_pages_dir)
    else:
        scan_pdf(args.pdf, args.keyword, as_json=args.json)


if __name__ == "__main__":
    main()
