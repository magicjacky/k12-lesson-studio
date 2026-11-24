#!/usr/bin/env python3
"""
md_to_docx.py — Printable A4 Teaching Word (.docx) Converter (k12-lesson-studio v5.1)

Supports:
- Lesson plans, unit pacing tables, student exams, teacher red-ink keys, grading reports & cut-out remediation cards
- Teacher crimson red-ink styling (#C83228) for 【答案】/【参考答案】/【解析】/【评分标准】/【易错警示】 and inline [红字:...]
- Student answer-leak protection in --mode student
- Printable dashed writing lines via [答题线:N]
- Exam student info header bar via [试卷抬头]
- Explicit Word page breaks via [分页] or ===PAGE_BREAK===
- Bordered callout boxes (> / > [!口诀] / > [!警示]) and printable checkboxes (- [ ] ...)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

COLOR_PRIMARY = RGBColor(0x16, 0x32, 0x40)
COLOR_ACCENT = RGBColor(0x1F, 0x6E, 0x7A)
COLOR_MUTED = RGBColor(0x5A, 0x6B, 0x75)
COLOR_CRIMSON = RGBColor(0xC8, 0x32, 0x28)
COLOR_GOLD_DARK = RGBColor(0x9A, 0x67, 0x12)

HEX_HEADER_BG = "1F6E7A"
HEX_ALT_ROW = "F2F7F6"
HEX_QUOTE_BG = "F7F9F8"
HEX_WARN_BG = "FDF6EC"
HEX_BORDER = "C8D6D3"
HEX_ACCENT = "1F6E7A"
HEX_CRIMSON = "C83228"

TEACHER_TAG_RE = re.compile(r"^(?:\*\*)?(【(?:参考)?答案】|【解析】|【评分标准】|【得分点】|【易错警示】)(?:\*\*)?\s*(.*)$")


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


def add_inline_markdown(paragraph, text: str, size_pt=10.5, default_color=COLOR_PRIMARY):
    # Normalize **[红字:...]** -> [红字:...] so nested bold+red never leaves literal brackets
    text = re.sub(r"\*\*\[红字:([^\]]+)\]\*\*", r"[红字:\1]", text)
    parts = re.split(r"(\[红字:[^\]]+\]|\*\*.*?\*\*|`.*?`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("[红字:") and part.endswith("]"):
            inner_red = part[4:-1].replace("**", "")
            r = paragraph.add_run(inner_red)
            set_run_font(r, size_pt=size_pt, bold=True, color=COLOR_CRIMSON)
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            inner = part[2:-2]
            is_red = any(k in inner for k in ("【答案】", "【参考答案】", "【解析】", "【评分标准】", "【易错警示】"))
            r = paragraph.add_run(inner)
            set_run_font(r, size_pt=size_pt, bold=True, color=COLOR_CRIMSON if is_red else default_color)
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


def add_exam_header(doc: Document, size_pt: float):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    pPr.append(
        parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'<w:bottom w:val="double" w:sz="6" w:space="4" w:color="{HEX_ACCENT}"/>'
            f'</w:pBdr>'
        )
    )
    r = p.add_run("班级：____________    姓名：____________    学号：____________    得分：____________")
    set_run_font(r, size_pt=size_pt, bold=True, color=COLOR_PRIMARY)


def add_dashed_answer_lines(doc: Document, count: int):
    for _ in range(max(1, min(12, count))):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        pPr = p._p.get_or_add_pPr()
        pPr.append(
            parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                '<w:bottom w:val="dashed" w:sz="4" w:space="1" w:color="9AA8B0"/>'
                '</w:pBdr>'
            )
        )
        r = p.add_run(" ")
        set_run_font(r, size_pt=10.5)


def convert(md_path: pathlib.Path, docx_path: pathlib.Path, compact: bool = False, mode: str = "default"):
    doc = Document()
    for sec in doc.sections:
        sec.page_width = Cm(21.0)
        sec.page_height = Cm(29.7)
        margin = Cm(1.6 if mode == "card" else (1.8 if compact else 2.1))
        sec.top_margin = margin
        sec.bottom_margin = margin
        sec.left_margin = margin
        sec.right_margin = margin

    body_pt = 9.5 if (compact or mode == "card") else 10.5
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
                pPr.append(
                    parse_xml(
                        f'<w:pBdr {nsdecls("w")}>'
                        f'<w:top w:val="single" w:sz="6" w:space="4" w:color="{HEX_BORDER}"/>'
                        f'<w:bottom w:val="single" w:sz="6" w:space="4" w:color="{HEX_BORDER}"/>'
                        f'<w:left w:val="single" w:sz="12" w:space="6" w:color="{HEX_ACCENT}"/>'
                        f'<w:right w:val="single" w:sz="6" w:space="4" w:color="{HEX_BORDER}"/>'
                        f'</w:pBdr>'
                    )
                )
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

        if s in {"[分页]", "===PAGE_BREAK===", "\\f"}:
            doc.add_page_break()
            i += 1
            continue

        if s in {"[试卷抬头]", "<!-- EXAM_HEADER -->"}:
            add_exam_header(doc, body_pt)
            i += 1
            continue

        m_ans_line = re.fullmatch(r"\[答题线:(\d+)\]", s)
        if m_ans_line:
            add_dashed_answer_lines(doc, int(m_ans_line.group(1)))
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

        # Teacher red-ink answer/rubric lines
        m_teacher = TEACHER_TAG_RE.match(s)
        if m_teacher:
            if mode == "student":
                print(f"[md_to_docx] Skipped answer line in student mode: {s[:40]}", file=sys.stderr)
                i += 1
                continue
            tag_lbl, body_txt = m_teacher.group(1), m_teacher.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.3)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2.5)
            r_tag = p.add_run(tag_lbl + " ")
            set_run_font(r_tag, size_pt=body_pt, bold=True, color=COLOR_CRIMSON)
            add_inline_markdown(p, body_txt, size_pt=body_pt, default_color=COLOR_CRIMSON)
            i += 1
            continue

        if s.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(7)
            r = p.add_run(s[2:].strip())
            set_run_font(r, size_pt=15.5 if compact else 17.5, bold=True, color=COLOR_CRIMSON if mode == "teacher" else COLOR_PRIMARY)
        elif s.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(9)
            p.paragraph_format.space_after = Pt(3.5)
            r = p.add_run(s[3:].strip())
            set_run_font(r, size_pt=12 if compact else 13, bold=True, color=COLOR_ACCENT)
        elif s.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(s[4:].strip())
            set_run_font(r, size_pt=10.8 if compact else 11.5, bold=True, color=COLOR_PRIMARY)
        elif s.startswith("> "):
            q_body = s[2:].strip()
            is_alert = False
            m_alert = re.match(r"^\[!([^\]]+)\]\s*(.*)$", q_body)
            if m_alert:
                is_alert = True
                q_body = f"**【{m_alert.group(1)}】** {m_alert.group(2)}"
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.35)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(4)
            pPr = p._p.get_or_add_pPr()
            bdr_color = HEX_CRIMSON if is_alert else HEX_ACCENT
            bg_color = HEX_WARN_BG if is_alert else HEX_QUOTE_BG
            pPr.append(
                parse_xml(
                    f'<w:pBdr {nsdecls("w")}>'
                    f'<w:left w:val="single" w:sz="18" w:space="6" w:color="{bdr_color}"/>'
                    f'</w:pBdr>'
                )
            )
            pPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>'))
            add_inline_markdown(p, q_body, size_pt=body_pt - 0.3, default_color=COLOR_GOLD_DARK if is_alert else COLOR_MUTED)
        elif s.startswith("- [ ] ") or s.startswith("* [ ] "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.45)
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run("□ ")
            set_run_font(r, size_pt=body_pt + 0.5, bold=True, color=COLOR_ACCENT)
            add_inline_markdown(p, s[6:].strip(), size_pt=body_pt)
        elif s.startswith("- ") or s.startswith("* "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.45)
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
    print(f"Saved Word document: {docx_path} ({docx_path.stat().st_size} bytes, mode={mode})")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("md", type=pathlib.Path)
    ap.add_argument("docx", type=pathlib.Path)
    ap.add_argument("--compact", action="store_true", help="Compact A4 layout for 2-4 page printing")
    ap.add_argument("--mode", choices=["default", "student", "teacher", "card"], default="default")
    args = ap.parse_args()
    convert(args.md, args.docx, compact=args.compact, mode=args.mode)


if __name__ == "__main__":
    main()
