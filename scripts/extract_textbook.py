#!/usr/bin/env python3
"""Scan a textbook PDF, locate a unit, export excerpt PDF, and dump raw text for verification."""
import argparse
import pathlib
import fitz


def scan_pdf(pdf_path: pathlib.Path, keyword: str):
    doc = fitz.open(str(pdf_path))
    print(f"File: {pdf_path.name} | Total pages: {len(doc)}")
    print("\n--- Front pages (1..8) ---")
    for i in range(min(8, len(doc))):
        lines = [l.strip() for l in doc[i].get_text().splitlines() if l.strip()]
        print(f"PDF P{i+1:02d}: " + " | ".join(lines[:6])[:160])

    if keyword:
        print(f"\n--- Keyword hits for '{keyword}' ---")
        for i in range(len(doc)):
            txt = doc[i].get_text()
            if keyword in txt:
                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                print(f"PDF P{i+1:03d}: " + " | ".join(lines[:5])[:160])


def extract_range(pdf_path: pathlib.Path, start_page: int, end_page: int, out_pdf: pathlib.Path, out_txt: pathlib.Path | None):
    doc = fitz.open(str(pdf_path))
    s = max(0, start_page - 1)
    e = min(len(doc) - 1, end_page - 1)
    excerpt = fitz.open()
    excerpt.insert_pdf(doc, from_page=s, to_page=e)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    excerpt.save(str(out_pdf))
    print(f"Saved excerpt PDF: {out_pdf} ({e - s + 1} pages, {out_pdf.stat().st_size} bytes)")

    if out_txt:
        parts = []
        for idx in range(s, e + 1):
            parts.append(f"===== PDF Page {idx + 1} =====\n{doc[idx].get_text()}\n")
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text("\n".join(parts), encoding="utf-8")
        print(f"Saved extracted text: {out_txt} ({out_txt.stat().st_size} bytes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=pathlib.Path, help="Path to textbook PDF")
    ap.add_argument("--keyword", default="", help="Keyword to search in pages")
    ap.add_argument("--start", type=int, help="1-based start PDF page to extract")
    ap.add_argument("--end", type=int, help="1-based end PDF page to extract")
    ap.add_argument("--out-pdf", type=pathlib.Path, help="Output excerpt PDF path")
    ap.add_argument("--out-txt", type=pathlib.Path, help="Optional raw text dump path")
    args = ap.parse_args()

    if args.start and args.end and args.out_pdf:
        extract_range(args.pdf, args.start, args.end, args.out_pdf, args.out_txt)
    else:
        scan_pdf(args.pdf, args.keyword)


if __name__ == "__main__":
    main()
