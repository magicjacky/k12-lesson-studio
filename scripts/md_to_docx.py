#!/usr/bin/env python3
"""Convert clean teaching Markdown into formatted printable A4 Word (.docx) documents."""
import argparse
import pathlib
import re
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

COLOR_PRIMARY = RGBColor(0x16, 0x32, 0x40)
COLOR_ACCENT = RGBColor(0x1F, 0x6E, 0x7A)
COLOR_MUTED = RGBColor(0x5A, 0x6B, 0x75)
HEX_HEADER_BG = "1F6E7A"
HEX_ALT_ROW = "F2F7F6"
HEX_QUOTE_BG = "F7F9F8"
HEX_BORDER = "C8D6D3"


def set_run_font(run, name="微软雅黑", size_pt=10.5, bold=False, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size_pt)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_inline_markdown(paragraph, text, size_pt=10.5, default_color=COLOR_PRIMARY):
    parts = re.split(r"(\*\*.*?\*\*|`.*?`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = paragraph.add_run(part[2:-2])
            set_run_font(r, size_pt=size_pt, bold=True, color=default_color)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = paragraph.add_run(part[1:-1])
            set_run_font(r, name="Consolas", size_pt=size_pt - 0.5, bold=False, color=COLOR_ACCENT)
        else:
            r = paragraph.add_run(part)
            set_run_font(r, size_pt=size_pt, bold=False, color=default_color)


def style_table(table):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)
    for r_idx, row in enumerate(table.rows):
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            margins = parse_xml(
                f'<w:tcMar {nsdecls("w")}>'
                '<w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/>'
                '<w:left w:w="120" w:type="dxa"/><w:right w:w="120" w:type="dxa"/>'
                '</w:tcMar>'
            )
            tcPr.append(margins)
            if r_idx == 0:
                tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_HEADER_BG}"/>'))
            elif r_idx % 2 == 0:
                tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_ALT_ROW}"/>'))


def convert(md_path: pathlib.Path, docx_path: pathlib.Path, compact: bool = False):
    doc = Document()
    for sec in doc.sections:
        sec.page_width = Cm(21.0)
        sec.page_height = Cm(29.7)
        margin = Cm(1.8 if compact else 2.2)
        sec.top_margin = margin
        sec.bottom_margin = margin
        sec.left_margin = margin
        sec.right_margin = margin

    body_pt = 9.5 if compact else 10.5
    lines = md_path.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    in_code = False
    code_buf = []

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if s.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                pPr = p._p.get_or_add_pPr()
                pPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_QUOTE_BG}"/>'))
                r = p.add_run("\n".join(code_buf))
                set_run_font(r, name="微软雅黑", size_pt=body_pt - 0.5, color=COLOR_PRIMARY)
            i += 1
            continue
        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        if not s or s == "---":
            i += 1
            continue

        # Markdown table
        if s.startswith("|") and s.endswith("|"):
            tlines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tlines.append(lines[i].strip())
                i += 1
            rows_data = []
            for tl in tlines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                if all(re.fullmatch(r"[:\- ]+", c or "-") for c in cells):
                    continue
                rows_data.append(cells)
            if rows_data:
                ncols = max(len(r) for r in rows_data)
                tbl = doc.add_table(rows=len(rows_data), cols=ncols)
                for r_idx, rdata in enumerate(rows_data):
                    for c_idx in range(ncols):
                        val = rdata[c_idx] if c_idx < len(rdata) else ""
                        p = tbl.cell(r_idx, c_idx).paragraphs[0]
                        p.paragraph_format.space_before = Pt(1)
                        p.paragraph_format.space_after = Pt(1)
                        if r_idx == 0:
                            r = p.add_run(re.sub(r"\*\*", "", val))
                            set_run_font(r, size_pt=body_pt - 0.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
                        else:
                            add_inline_markdown(p, val, size_pt=body_pt - 0.5)
                style_table(tbl)
            continue

        if s.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(s[2:].strip())
            set_run_font(r, size_pt=16 if compact else 18, bold=True, color=COLOR_PRIMARY)
        elif s.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(s[3:].strip())
            set_run_font(r, size_pt=12.5 if compact else 13.5, bold=True, color=COLOR_ACCENT)
        elif s.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(7)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(s[4:].strip())
            set_run_font(r, size_pt=11 if compact else 11.5, bold=True, color=COLOR_PRIMARY)
        elif s.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.4)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(4)
            pPr = p._p.get_or_add_pPr()
            pPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_QUOTE_BG}"/>'))
            add_inline_markdown(p, s[2:].strip(), size_pt=body_pt - 0.5, default_color=COLOR_MUTED)
        elif s.startswith("- ") or s.startswith("* "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run("• ")
            set_run_font(r, size_pt=body_pt, bold=True, color=COLOR_ACCENT)
            add_inline_markdown(p, s[2:].strip(), size_pt=body_pt)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.25
            add_inline_markdown(p, s, size_pt=body_pt)
        i += 1

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"Saved Word document: {docx_path} ({docx_path.stat().st_size} bytes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("md", type=pathlib.Path)
    ap.add_argument("docx", type=pathlib.Path)
    ap.add_argument("--compact", action="store_true", help="Compact A4 layout for 2-4 page printing")
    args = ap.parse_args()
    convert(args.md, args.docx, compact=args.compact)


if __name__ == "__main__":
    main()
