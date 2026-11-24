#!/usr/bin/env python3
"""
ppt_kit.py — Reusable 16:9 Museum-Magazine All-Subject Editable Teaching PPTX Builder (k12-lesson-studio v5.1)

Guarantees:
- 16:9 canvas (13.333 in x 7.5 in) with safe non-overlapping grids
- All-subject curated palettes (math, chinese, english, science, physics, chemistry, biology, history, geography, morality)
- Zero-distortion aspect-fit image cropping via Pillow + OOXML crop attributes
- 100% native editable text frames, tables & vector diagrams (Seewo / WPS / PowerPoint compatible)
- All-subject native vector schematics: process timeline, A-vs-B comparison, concept hub, multi-subject blueprints, plus math cone/cylinder helpers
- Reusable full-slide builders: hero cover, split visual gallery, offline MP4 video theater, 3-tier practice, 2x2 pitfall matrix, 40:60 table summary
- Native OOXML slide fade transitions (<p:transition>) & mandatory speaker notes
"""
from __future__ import annotations

import pathlib
from typing import Sequence

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.util import Inches, Pt

FONT_CN = "Microsoft YaHei"
FONT_NUM = "Georgia"


def rgb(h: str) -> RGBColor:
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


THEMES = {
    "math": {
        "dark_bg": rgb("#0B1A20"),
        "dark_panel": rgb("#11262F"),
        "light_bg": rgb("#F6F2EA"),
        "sand_card": rgb("#ECE5D8"),
        "ink": rgb("#14262B"),
        "ink_light": rgb("#F7F4EC"),
        "muted": rgb("#5B6B70"),
        "muted_dark": rgb("#9FB4BC"),
        "primary": rgb("#155E68"),
        "accent": rgb("#C84B31"),
        "accent_bright": rgb("#E05A3A"),
        "gold": rgb("#C69749"),
        "gold_bright": rgb("#E2B45A"),
    },
    "chinese": {
        "dark_bg": rgb("#132624"),
        "dark_panel": rgb("#1B3431"),
        "light_bg": rgb("#F7F3E8"),
        "sand_card": rgb("#EDE5D5"),
        "ink": rgb("#1A2623"),
        "ink_light": rgb("#F7F3E8"),
        "muted": rgb("#5E6B66"),
        "muted_dark": rgb("#A6B8B1"),
        "primary": rgb("#22577A"),
        "accent": rgb("#B83B2A"),
        "accent_bright": rgb("#D6523E"),
        "gold": rgb("#C49642"),
        "gold_bright": rgb("#DFB35C"),
    },
    "english": {
        "dark_bg": rgb("#18243E"),
        "dark_panel": rgb("#223254"),
        "light_bg": rgb("#FBF7EE"),
        "sand_card": rgb("#F1E9D8"),
        "ink": rgb("#172033"),
        "ink_light": rgb("#FBF7EE"),
        "muted": rgb("#5B677D"),
        "muted_dark": rgb("#A9B8D0"),
        "primary": rgb("#2563EB"),
        "accent": rgb("#E85D3F"),
        "accent_bright": rgb("#F27559"),
        "gold": rgb("#D49B2A"),
        "gold_bright": rgb("#F4B942"),
    },
    "science": {
        "dark_bg": rgb("#09131F"),
        "dark_panel": rgb("#122236"),
        "light_bg": rgb("#F3F6F9"),
        "sand_card": rgb("#E4ECF2"),
        "ink": rgb("#102A43"),
        "ink_light": rgb("#F3F6F9"),
        "muted": rgb("#52687C"),
        "muted_dark": rgb("#9BB1C5"),
        "primary": rgb("#0F8B74"),
        "accent": rgb("#D97706"),
        "accent_bright": rgb("#F59E0B"),
        "gold": rgb("#38BDF8"),
        "gold_bright": rgb("#7DD3FC"),
    },
    "biology": {
        "dark_bg": rgb("#0B1E19"),
        "dark_panel": rgb("#132F28"),
        "light_bg": rgb("#F4F8F5"),
        "sand_card": rgb("#E5EFE8"),
        "ink": rgb("#122A22"),
        "ink_light": rgb("#F3FAF6"),
        "muted": rgb("#526D63"),
        "muted_dark": rgb("#9EC0B3"),
        "primary": rgb("#0F8B6D"),
        "accent": rgb("#D96B27"),
        "accent_bright": rgb("#F58436"),
        "gold": rgb("#C99A3E"),
        "gold_bright": rgb("#E8BC5A"),
    },
}

THEME_ALIASES = {
    "physics": "science",
    "chemistry": "science",
    "history": "chinese",
    "geography": "chinese",
    "morality": "chinese",
    "politics": "chinese",
}


def get_theme(name: str = "math") -> dict:
    key = THEME_ALIASES.get(name.lower().strip(), name.lower().strip())
    return THEMES.get(key, THEMES["math"])


def create_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_blank_slide(prs: Presentation, bg_color: RGBColor, transition: str = "fade"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg_color
    if transition:
        add_transition(slide, transition)
    return slide


def add_transition(slide, kind: str = "fade", speed: str = "med"):
    sld = slide._element
    for old in list(sld.findall("{http://schemas.openxmlformats.org/presentationml/2006/main}transition")):
        sld.remove(old)
    tag = "fade" if kind not in {"fade", "push", "wipe"} else kind
    xml = f'<p:transition {nsdecls("p")} spd="{speed}"><p:{tag}/></p:transition>'
    sld.append(parse_xml(xml))


def set_notes(slide, text: str):
    ns = slide.notes_slide
    tf = ns.notes_text_frame
    tf.clear()
    tf.paragraphs[0].text = text.strip()


def add_picture_cover(slide, img_path: str | pathlib.Path, x: float, y: float, w: float, h: float):
    """Insert an image filling (x, y, w, h) with center aspect-crop so 1:1 / 4:3 / 16:9 images never stretch."""
    p = pathlib.Path(img_path)
    with Image.open(p) as im:
        iw, ih = im.size
    pic = slide.shapes.add_picture(str(p), Inches(x), Inches(y))
    src_ratio = iw / max(1, ih)
    dst_ratio = w / max(0.01, h)
    if abs(src_ratio - dst_ratio) > 0.015:
        if src_ratio > dst_ratio:
            crop_total = 1.0 - (dst_ratio / src_ratio)
            pic.crop_left = round(crop_total / 2.0, 5)
            pic.crop_right = round(crop_total / 2.0, 5)
        else:
            crop_total = 1.0 - (src_ratio / dst_ratio)
            pic.crop_top = round(crop_total / 2.0, 5)
            pic.crop_bottom = round(crop_total / 2.0, 5)
    pic.left = Inches(x)
    pic.top = Inches(y)
    pic.width = Inches(w)
    pic.height = Inches(h)
    return pic


def add_rect(slide, x, y, w, h, fill_rgb=None, line_rgb=None, line_pt=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill_rgb is not None:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill_rgb
    else:
        sh.fill.background()
    if line_rgb is not None:
        sh.line.color.rgb = line_rgb
        sh.line.width = Pt(line_pt)
    else:
        sh.line.fill.background()
    return sh


def add_text(
    slide,
    x,
    y,
    w,
    h,
    text: str,
    size: float = 16,
    color: RGBColor = None,
    bold: bool = False,
    font_name: str = FONT_CN,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    line_spacing: float = 1.25,
):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.name = font_name
        r.font.size = Pt(size)
        r.font.bold = bold
        if color is not None:
            r.font.color.rgb = color
    return tb


def add_chrome(slide, theme: dict, page_no: int, total_pages: int, tag: str, course_label: str, dark: bool = False):
    """Consistent non-overlapping header eyebrow + bottom hairline & page number."""
    fg = theme["gold_bright"] if dark else theme["gold"]
    muted = theme["muted_dark"] if dark else theme["muted"]
    tb = slide.shapes.add_textbox(Inches(0.60), Inches(0.36), Inches(5.8), Inches(0.34))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r1 = p.add_run()
    r1.text = f"{page_no:02d}  "
    r1.font.name = FONT_NUM
    r1.font.size = Pt(13)
    r1.font.bold = True
    r1.font.color.rgb = fg
    r2 = p.add_run()
    r2.text = f"/  {tag}"
    r2.font.name = FONT_CN
    r2.font.size = Pt(12)
    r2.font.color.rgb = muted

    add_text(slide, 7.6, 0.36, 5.13, 0.32, course_label, size=11.5, color=muted, align=PP_ALIGN.RIGHT)
    add_rect(slide, 0.60, 6.96, 12.13, 0.012, fill_rgb=fg)
    add_text(slide, 0.60, 7.04, 6.0, 0.28, course_label, size=11, color=muted)
    add_text(
        slide,
        11.2,
        7.04,
        1.53,
        0.28,
        f"{page_no:02d} / {total_pages:02d}",
        size=11,
        color=fg,
        font_name=FONT_NUM,
        align=PP_ALIGN.RIGHT,
    )


def add_card(slide, x, y, w, h, fill_rgb, accent_top_rgb=None, border_rgb=None, border_pt=0.75):
    """Clean Swiss editorial panel with optional slim top accent rule."""
    card = add_rect(slide, x, y, w, h, fill_rgb=fill_rgb, line_rgb=border_rgb, line_pt=border_pt)
    if accent_top_rgb is not None:
        add_rect(slide, x, y, w, 0.045, fill_rgb=accent_top_rgb)
    return card


def add_pill(slide, x, y, w, h, text: str, fill_rgb, text_rgb, size: float = 12, bold: bool = True, border_rgb=None):
    """Rounded editorial pill tag (100% native editable)."""
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = 0.45
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill_rgb
    if border_rgb is not None:
        sh.line.color.rgb = border_rgb
        sh.line.width = Pt(0.8)
    else:
        sh.line.fill.background()
    tf = sh.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = FONT_CN
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = text_rgb
    return sh


# ==============================================================================
# FULL-SLIDE BUILDERS (All-Subject Reusable 16:9 Museum-Magazine Layouts)
# ==============================================================================

def add_hero_slide(
    prs: Presentation,
    theme: dict,
    img_path: str | pathlib.Path,
    eyebrow: str,
    title: str,
    subtitle: str,
    formula_label: str,
    formula_text: str,
    footer_left: str,
    total_pages: int,
    notes: str,
):
    slide = add_blank_slide(prs, theme["dark_bg"])
    add_picture_cover(slide, img_path, 0, 0, 13.333, 7.5)
    add_text(slide, 0.72, 0.62, 5.6, 0.34, eyebrow, size=12, color=theme["gold_bright"])
    add_text(slide, 0.72, 1.35, 5.8, 1.35, title, size=44, color=theme["ink_light"], bold=True, line_spacing=1.12)
    add_rect(slide, 0.72, 2.86, 2.1, 0.025, fill_rgb=theme["gold_bright"])
    add_text(slide, 0.72, 3.12, 5.4, 1.25, subtitle, size=17, color=theme["muted_dark"], line_spacing=1.45)
    add_text(slide, 0.72, 4.90, 5.2, 0.34, formula_label, size=12, color=theme["gold_bright"])
    add_text(slide, 0.72, 5.28, 5.6, 0.76, formula_text, size=30, color=theme["ink_light"], bold=True, font_name=FONT_NUM)
    add_text(slide, 0.72, 6.86, 6.0, 0.32, footer_left, size=11.5, color=theme["muted_dark"])
    add_text(slide, 11.4, 6.86, 1.3, 0.32, f"01 / {total_pages:02d}", size=11.5, color=theme["gold_bright"], font_name=FONT_NUM, align=PP_ALIGN.RIGHT)
    set_notes(slide, notes)
    return slide


def add_split_visual_slide(
    prs: Presentation,
    theme: dict,
    page_no: int,
    total_pages: int,
    tag: str,
    course_label: str,
    title: str,
    img_path: str | pathlib.Path,
    blocks: Sequence[tuple[str, str]],
    bottom_banner: str = "",
    dark: bool = False,
    image_on_left: bool = True,
    notes: str = "",
):
    """46:54 editorial split slide for real-world intro (P02), counterexample contrast (P06), or stage wrap-up (P11)."""
    bg = theme["dark_bg"] if dark else theme["light_bg"]
    fg = theme["ink_light"] if dark else theme["ink"]
    muted = theme["muted_dark"] if dark else theme["muted"]
    card_bg = theme["dark_panel"] if dark else theme["sand_card"]
    accent = theme["gold_bright"] if dark else theme["primary"]

    slide = add_blank_slide(prs, bg)
    add_chrome(slide, theme, page_no, total_pages, tag, course_label, dark=dark)
    add_text(slide, 0.60, 0.78, 12.13, 0.56, title, size=26, color=fg, bold=True)

    content_h = 4.55 if bottom_banner else 5.25
    if image_on_left:
        ix, iw, tx, tw = 0.60, 5.55, 6.45, 6.28
    else:
        tx, tw, ix, iw = 0.60, 6.28, 7.18, 5.55

    add_rect(slide, ix - 0.03, 1.48 - 0.03, iw + 0.06, content_h + 0.06, fill_rgb=card_bg, line_rgb=theme["gold"], line_pt=0.9)
    add_picture_cover(slide, img_path, ix, 1.48, iw, content_h)

    n_blk = max(1, min(3, len(blocks)))
    gap = 0.20
    bh = (content_h - gap * (n_blk - 1)) / n_blk
    for idx, (b_head, b_body) in enumerate(blocks[:3]):
        by = 1.48 + idx * (bh + gap)
        top_c = theme["accent_bright"] if idx == n_blk - 1 else accent
        add_card(slide, tx, by, tw, bh, fill_rgb=card_bg, accent_top_rgb=top_c, border_rgb=theme["gold"] if dark else None, border_pt=0.6)
        add_text(slide, tx + 0.22, by + 0.14, tw - 0.44, 0.34, b_head, size=15, color=top_c, bold=True)
        add_text(slide, tx + 0.22, by + 0.50, tw - 0.44, max(0.36, bh - 0.60), b_body, size=13.5, color=fg if idx == 0 else muted, line_spacing=1.32)

    if bottom_banner:
        ban_fill = theme["dark_panel"] if dark else theme["primary"]
        add_rect(slide, 0.60, 6.18, 12.13, 0.62, fill_rgb=ban_fill, line_rgb=theme["gold_bright"] if dark else None, line_pt=0.8)
        add_text(slide, 0.84, 6.26, 11.65, 0.46, bottom_banner, size=14.5, color=theme["ink_light"], bold=True, valign=MSO_ANCHOR.MIDDLE)

    set_notes(slide, notes)
    return slide


def add_video_slide(
    prs: Presentation,
    theme: dict,
    mp4_path: str | pathlib.Path,
    poster_path: str | pathlib.Path,
    page_no: int,
    total_pages: int,
    tag: str,
    course_label: str,
    title: str,
    hint: str,
    beats: Sequence[tuple[str, str, str]],
    badge_title: str,
    badge_desc: str,
    notes: str,
):
    """Dark theater slide with offline embedded playable MP4 video + 3-step observation beats."""
    slide = add_blank_slide(prs, theme["dark_bg"])
    add_chrome(slide, theme, page_no, total_pages, tag, course_label, dark=True)
    add_text(slide, 0.60, 0.76, 8.6, 0.56, title, size=27, color=theme["ink_light"], bold=True)
    add_text(slide, 9.30, 0.86, 3.43, 0.36, hint, size=12, color=theme["gold_bright"], align=PP_ALIGN.RIGHT)

    vx, vy, vw, vh = 0.60, 1.50, 8.55, 4.88
    add_rect(slide, vx - 0.04, vy - 0.04, vw + 0.08, vh + 0.08, fill_rgb=theme["dark_panel"], line_rgb=theme["gold_bright"], line_pt=1.0)
    slide.shapes.add_movie(
        str(mp4_path),
        Inches(vx),
        Inches(vy),
        Inches(vw),
        Inches(vh),
        poster_frame_image=str(poster_path),
        mime_type="video/mp4",
    )

    rx, rw = 9.48, 3.25
    add_text(slide, rx, 1.52, rw, 0.34, "观察三步节拍", size=13, color=theme["gold_bright"], bold=True)
    add_rect(slide, rx, 1.90, rw, 0.015, fill_rgb=theme["gold"])
    for idx, (num, head, desc) in enumerate(beats[:3]):
        by = 2.08 + idx * 1.12
        tb = slide.shapes.add_textbox(Inches(rx), Inches(by), Inches(rw), Inches(0.36))
        p = tb.text_frame.paragraphs[0]
        r1 = p.add_run()
        r1.text = f"{num}  "
        r1.font.name = FONT_NUM
        r1.font.size = Pt(16)
        r1.font.bold = True
        r1.font.color.rgb = theme["gold_bright"]
        r2 = p.add_run()
        r2.text = head
        r2.font.name = FONT_CN
        r2.font.size = Pt(15.5)
        r2.font.bold = True
        r2.font.color.rgb = theme["ink_light"]
        add_text(slide, rx, by + 0.40, rw, 0.56, desc, size=12.5, color=theme["muted_dark"], line_spacing=1.35)

    add_rect(slide, rx, 5.44, rw, 0.96, fill_rgb=theme["dark_panel"], line_rgb=theme["gold"], line_pt=0.8)
    add_text(slide, rx + 0.16, 5.54, rw - 0.32, 0.32, badge_title, size=13, color=theme["gold_bright"], bold=True)
    add_text(slide, rx + 0.16, 5.88, rw - 0.32, 0.46, badge_desc, size=11.5, color=theme["muted_dark"], line_spacing=1.25)
    set_notes(slide, notes)
    return slide


def add_tiered_practice_slide(
    prs: Presentation,
    theme: dict,
    page_no: int,
    total_pages: int,
    tag: str,
    course_label: str,
    title: str,
    tiers: Sequence[tuple[str, str, str, str]],
    bottom_tip: str,
    notes: str,
):
    """Swiss editorial 3-column tiered practice slide (tiers: [(badge, head, stem, hint_or_ans), ...])."""
    slide = add_blank_slide(prs, theme["light_bg"])
    add_chrome(slide, theme, page_no, total_pages, tag, course_label, dark=False)
    add_text(slide, 0.60, 0.78, 12.13, 0.54, title, size=26, color=theme["ink"], bold=True)

    accents = [theme["primary"], theme["gold"], theme["accent"]]
    gap = 0.28
    cw = (12.13 - 2 * gap) / 3.0
    cy, ch = 1.50, 4.52
    for idx, (badge, head, stem, ans_tip) in enumerate(tiers[:3]):
        cx = 0.60 + idx * (cw + gap)
        ac = accents[idx % 3]
        add_card(slide, cx, cy, cw, ch, fill_rgb=theme["sand_card"], accent_top_rgb=ac)
        add_pill(slide, cx + 0.20, cy + 0.20, 1.35, 0.34, badge, fill_rgb=ac, text_rgb=theme["ink_light"], size=11.5)
        add_text(slide, cx + 0.20, cy + 0.66, cw - 0.40, 0.40, head, size=16.5, color=theme["ink"], bold=True)
        add_text(slide, cx + 0.20, cy + 1.14, cw - 0.40, 2.15, stem, size=14, color=theme["ink"], line_spacing=1.36)
        add_rect(slide, cx + 0.20, cy + 3.40, cw - 0.40, 0.014, fill_rgb=ac)
        add_text(slide, cx + 0.20, cy + 3.52, cw - 0.40, 0.86, ans_tip, size=12.5, color=theme["muted"], line_spacing=1.30)

    add_rect(slide, 0.60, 6.18, 12.13, 0.60, fill_rgb=theme["dark_bg"])
    add_text(slide, 0.84, 6.26, 11.65, 0.44, bottom_tip, size=14, color=theme["gold_bright"], bold=True, valign=MSO_ANCHOR.MIDDLE)
    set_notes(slide, notes)
    return slide


def add_pitfall_matrix_slide(
    prs: Presentation,
    theme: dict,
    page_no: int,
    total_pages: int,
    tag: str,
    course_label: str,
    title: str,
    pitfalls: Sequence[tuple[str, str, str]],
    checklist_bar: str,
    notes: str,
):
    """2x2 pitfall & rescue matrix slide (pitfalls: [(pitfall_title, wrong_trap, rescue_rule), ...])."""
    slide = add_blank_slide(prs, theme["light_bg"])
    add_chrome(slide, theme, page_no, total_pages, tag, course_label, dark=False)
    add_text(slide, 0.60, 0.78, 12.13, 0.54, title, size=26, color=theme["ink"], bold=True)

    gx, gy = 0.28, 0.22
    cw = (12.13 - gx) / 2.0
    ch = (4.50 - gy) / 2.0
    for idx, (p_title, wrong_txt, right_txt) in enumerate(pitfalls[:4]):
        r, c = divmod(idx, 2)
        cx = 0.60 + c * (cw + gx)
        cy = 1.50 + r * (ch + gy)
        add_card(slide, cx, cy, cw, ch, fill_rgb=theme["sand_card"], accent_top_rgb=theme["accent"])
        add_text(slide, cx + 0.20, cy + 0.14, cw - 0.40, 0.36, f"易错坑 {idx + 1} · {p_title}", size=15.5, color=theme["accent"], bold=True)
        add_text(slide, cx + 0.20, cy + 0.56, cw - 0.40, 0.66, f"典型错因：{wrong_txt}", size=13, color=theme["muted"], line_spacing=1.28)
        add_text(slide, cx + 0.20, cy + 1.28, cw - 0.40, 0.72, f"救场正解：{right_txt}", size=13.5, color=theme["primary"], bold=True, line_spacing=1.28)

    add_rect(slide, 0.60, 6.18, 12.13, 0.60, fill_rgb=theme["primary"])
    add_text(slide, 0.84, 6.26, 11.65, 0.44, checklist_bar, size=14, color=theme["ink_light"], bold=True, valign=MSO_ANCHOR.MIDDLE)
    set_notes(slide, notes)
    return slide


def add_summary_table_slide(
    prs: Presentation,
    theme: dict,
    page_no: int,
    total_pages: int,
    tag: str,
    course_label: str,
    left_eyebrow: str,
    left_title: str,
    left_formula: str,
    left_bullets: Sequence[str],
    table_headers: Sequence[str],
    table_rows: Sequence[Sequence[str]],
    homework_items: Sequence[tuple[str, str]],
    notes: str,
):
    """40:60 dark sculptural summary left panel + warm-linen native editable PPT table & homework right panel."""
    slide = add_blank_slide(prs, theme["light_bg"])
    # Left 40% sculptural dark column
    lw = 5.15
    add_rect(slide, 0, 0, lw, 7.5, fill_rgb=theme["dark_bg"])
    add_text(slide, 0.58, 0.52, lw - 1.0, 0.32, f"{page_no:02d}  /  {tag}", size=12.5, color=theme["gold_bright"], bold=True)
    add_text(slide, 0.58, 1.08, lw - 1.0, 0.32, left_eyebrow, size=12, color=theme["muted_dark"])
    add_text(slide, 0.58, 1.46, lw - 1.0, 1.05, left_title, size=28, color=theme["ink_light"], bold=True, line_spacing=1.18)
    add_rect(slide, 0.58, 2.66, 1.8, 0.024, fill_rgb=theme["gold_bright"])
    add_text(slide, 0.58, 2.90, lw - 1.0, 0.82, left_formula, size=24, color=theme["gold_bright"], bold=True, font_name=FONT_NUM)
    bullet_txt = "\n".join(f"•  {b}" for b in left_bullets)
    add_text(slide, 0.58, 3.92, lw - 1.0, 2.55, bullet_txt, size=13.5, color=theme["ink_light"], line_spacing=1.48)
    add_text(slide, 0.58, 6.96, lw - 1.0, 0.30, course_label, size=11, color=theme["muted_dark"])

    # Right 60% native editable table + homework
    rx, rw = 5.55, 7.18
    add_text(slide, rx, 0.52, rw, 0.32, f"{page_no:02d} / {total_pages:02d}", size=11.5, color=theme["gold"], font_name=FONT_NUM, align=PP_ALIGN.RIGHT)
    add_text(slide, rx, 0.96, rw, 0.42, "核心知识结构对比表（希沃可直接双击编辑）", size=17, color=theme["ink"], bold=True)

    nrows = 1 + len(table_rows)
    ncols = len(table_headers)
    th = min(3.15, 0.56 * nrows)
    t_shape = slide.shapes.add_table(nrows, ncols, Inches(rx), Inches(1.48), Inches(rw), Inches(th))
    tbl = t_shape.table
    for c_idx, h_txt in enumerate(table_headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme["primary"]
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = str(h_txt)
        r.font.name = FONT_CN
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = theme["ink_light"]

    for r_idx, row_vals in enumerate(table_rows, 1):
        for c_idx in range(ncols):
            cell = tbl.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = theme["sand_card"] if r_idx % 2 == 1 else theme["light_bg"]
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx > 0 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(row_vals[c_idx]) if c_idx < len(row_vals) else ""
            r.font.name = FONT_CN
            r.font.size = Pt(12)
            r.font.bold = c_idx == 0
            r.font.color.rgb = theme["ink"]

    hy = 1.48 + th + 0.30
    add_text(slide, rx, hy, rw, 0.36, "分层巩固作业清单", size=16, color=theme["ink"], bold=True)
    hw_h = max(0.56, (6.88 - (hy + 0.44) - 0.14 * max(0, len(homework_items[:3]) - 1)) / max(1, len(homework_items[:3])))
    for idx, (hw_tag, hw_desc) in enumerate(homework_items[:3]):
        iy = hy + 0.44 + idx * (hw_h + 0.14)
        add_card(slide, rx, iy, rw, hw_h, fill_rgb=theme["sand_card"], accent_top_rgb=theme["gold"] if idx == 1 else theme["primary"])
        add_pill(slide, rx + 0.16, iy + (hw_h - 0.32) / 2, 1.25, 0.32, hw_tag, fill_rgb=theme["primary"], text_rgb=theme["ink_light"], size=11)
        add_text(slide, rx + 1.56, iy + 0.08, rw - 1.74, hw_h - 0.14, hw_desc, size=12.5, color=theme["ink"], valign=MSO_ANCHOR.MIDDLE)

    set_notes(slide, notes)
    return slide


# ==============================================================================
# ALL-SUBJECT NATIVE EDITABLE VECTOR DIAGRAM BUILDERS (Zero AI Image Recycling!)
# ==============================================================================

def add_process_timeline_card(
    slide,
    theme: dict,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    steps: Sequence[tuple[str, str, str]],
    footer: str = "",
):
    """All-subject native vector 3-5 stage flow/timeline card (History, Chinese narrative, Science lab steps, Math solving)."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.85)
    add_text(slide, x + 0.24, y + 0.18, w - 0.48, 0.34, title, size=13.5, color=theme["gold_bright"], bold=True)

    items = list(steps[:5])
    n = max(1, len(items))
    inner_top = y + 0.68
    inner_bot = y + h - (0.64 if footer else 0.24)
    avail_h = inner_bot - inner_top

    if w >= 6.8 and n >= 3:
        # Horizontal stage cards with connecting arrows
        arrow_w = 0.22
        gap = 0.10
        cw = (w - 0.48 - (n - 1) * (arrow_w + 2 * gap)) / n
        for i, (num, head, desc) in enumerate(items):
            cx = x + 0.24 + i * (cw + arrow_w + 2 * gap)
            add_card(slide, cx, inner_top, cw, avail_h, fill_rgb=theme["dark_panel"], accent_top_rgb=theme["gold_bright"] if i == n - 1 else theme["primary"])
            add_pill(slide, cx + 0.14, inner_top + 0.16, min(0.86, cw - 0.28), 0.30, str(num), fill_rgb=theme["gold_bright"], text_rgb=theme["dark_bg"], size=11)
            add_text(slide, cx + 0.14, inner_top + 0.56, cw - 0.28, 0.42, head, size=14, color=theme["ink_light"], bold=True)
            add_text(slide, cx + 0.14, inner_top + 1.04, cw - 0.28, max(0.4, avail_h - 1.18), desc, size=12, color=theme["muted_dark"], line_spacing=1.30)
            if i < n - 1:
                ax = cx + cw + gap
                arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(inner_top + avail_h * 0.44), Inches(arrow_w), Inches(0.24))
                arr.fill.solid()
                arr.fill.fore_color.rgb = theme["gold_bright"]
                arr.line.fill.background()
    else:
        # Compact vertical stacked timeline
        gap = 0.12
        rh = (avail_h - gap * (n - 1)) / n
        for i, (num, head, desc) in enumerate(items):
            ry = inner_top + i * (rh + gap)
            add_rect(slide, x + 0.24, ry, w - 0.48, rh, fill_rgb=theme["dark_panel"], line_rgb=theme["gold"], line_pt=0.6)
            add_pill(slide, x + 0.36, ry + (rh - 0.30) / 2, 0.68, 0.30, str(num), fill_rgb=theme["gold_bright"], text_rgb=theme["dark_bg"], size=11)
            add_text(slide, x + 1.16, ry + 0.08, w - 1.52, 0.30, head, size=13.5, color=theme["ink_light"], bold=True)
            add_text(slide, x + 1.16, ry + 0.38, w - 1.52, max(0.24, rh - 0.44), desc, size=11.5, color=theme["muted_dark"], line_spacing=1.22)

    if footer:
        add_text(slide, x + 0.24, y + h - 0.46, w - 0.48, 0.32, footer, size=11.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)


def add_comparison_matrix_card(
    slide,
    theme: dict,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    left_header: str,
    right_header: str,
    rows: Sequence[tuple[str, str, str]],
    footer: str = "",
):
    """All-subject native vector A-vs-B contrast card (rows: [(dimension, side_A, side_B), ...])."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.85)
    add_text(slide, x + 0.24, y + 0.18, w - 0.48, 0.34, title, size=13.5, color=theme["gold_bright"], bold=True)

    dim_w = min(1.35, w * 0.22)
    col_w = (w - 0.48 - dim_w - 0.20) / 2.0
    lx = x + 0.24 + dim_w + 0.10
    rx = lx + col_w + 0.10
    hy = y + 0.62
    add_pill(slide, lx, hy, col_w, 0.36, left_header, fill_rgb=theme["primary"], text_rgb=theme["ink_light"], size=12)
    add_pill(slide, rx, hy, col_w, 0.36, right_header, fill_rgb=theme["accent"], text_rgb=theme["ink_light"], size=12)

    items = list(rows[:4])
    n = max(1, len(items))
    body_top = hy + 0.48
    body_bot = y + h - (0.58 if footer else 0.22)
    gap = 0.10
    rh = (body_bot - body_top - gap * (n - 1)) / n
    for idx, (dim_label, a_val, b_val) in enumerate(items):
        ry = body_top + idx * (rh + gap)
        add_rect(slide, x + 0.24, ry, dim_w, rh, fill_rgb=theme["dark_panel"])
        add_text(slide, x + 0.28, ry + 0.06, dim_w - 0.08, rh - 0.12, dim_label, size=11.5, color=theme["gold_bright"], bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

        add_rect(slide, lx, ry, col_w, rh, fill_rgb=theme["dark_panel"], line_rgb=theme["primary"], line_pt=0.7)
        add_text(slide, lx + 0.10, ry + 0.06, col_w - 0.20, rh - 0.12, a_val, size=11.5, color=theme["ink_light"], valign=MSO_ANCHOR.MIDDLE)

        add_rect(slide, rx, ry, col_w, rh, fill_rgb=theme["dark_panel"], line_rgb=theme["accent"], line_pt=0.7)
        add_text(slide, rx + 0.10, ry + 0.06, col_w - 0.20, rh - 0.12, b_val, size=11.5, color=theme["ink_light"], valign=MSO_ANCHOR.MIDDLE)

    if footer:
        add_text(slide, x + 0.24, y + h - 0.44, w - 0.48, 0.30, footer, size=11.5, color=theme["gold_bright"], bold=True, align=PP_ALIGN.CENTER)


def add_concept_hub_card(
    slide,
    theme: dict,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    hub_title: str,
    hub_sub: str,
    branches: Sequence[tuple[str, str]],
    footer: str = "",
):
    """All-subject central hub + 4 quadrant spoke cards (Chinese imagery, English grammar web, Science concept map)."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.85)
    add_text(slide, x + 0.24, y + 0.18, w - 0.48, 0.34, title, size=13.5, color=theme["gold_bright"], bold=True)

    mid_x = x + w / 2.0
    mid_y = y + 0.62 + (h - 0.62 - (0.52 if footer else 0.18)) / 2.0
    bw = (w - 0.72) * 0.42
    bh = min(1.06, (h - 1.80) * 0.38)
    v_gap = 0.44

    # Connecting cross hairlines behind hub and quadrant cards
    add_rect(slide, x + 0.48, mid_y - 0.01, w - 0.96, 0.02, fill_rgb=theme["gold"])
    add_rect(slide, mid_x - 0.01, y + 0.95, 0.02, h - 1.65, fill_rgb=theme["gold"])

    quad_coords = [
        (x + 0.24, mid_y - bh - v_gap),
        (x + w - 0.24 - bw, mid_y - bh - v_gap),
        (x + 0.24, mid_y + v_gap),
        (x + w - 0.24 - bw, mid_y + v_gap),
    ]
    for idx, (b_head, b_desc) in enumerate(branches[:4]):
        qx, qy = quad_coords[idx]
        add_card(slide, qx, qy, bw, bh, fill_rgb=theme["dark_panel"], accent_top_rgb=theme["primary"] if idx % 2 == 0 else theme["accent_bright"], border_rgb=theme["gold"], border_pt=0.6)
        add_text(slide, qx + 0.12, qy + 0.08, bw - 0.24, 0.28, b_head, size=12, color=theme["gold_bright"], bold=True)
        add_text(slide, qx + 0.12, qy + 0.36, bw - 0.24, max(0.28, bh - 0.42), b_desc, size=10.8, color=theme["ink_light"], line_spacing=1.20)

    hw, hh = min(1.85, w * 0.30), 0.74
    hub = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(mid_x - hw / 2), Inches(mid_y - hh / 2), Inches(hw), Inches(hh))
    hub.fill.solid()
    hub.fill.fore_color.rgb = theme["gold_bright"]
    hub.line.color.rgb = theme["ink_light"]
    hub.line.width = Pt(1.4)
    add_text(slide, mid_x - hw / 2 + 0.06, mid_y - 0.30, hw - 0.12, 0.32, hub_title, size=13.5, color=theme["dark_bg"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, mid_x - hw / 2 + 0.06, mid_y + 0.02, hw - 0.12, 0.28, hub_sub, size=10.5, color=theme["dark_bg"], bold=True, align=PP_ALIGN.CENTER)

    if footer:
        add_text(slide, x + 0.24, y + h - 0.44, w - 0.48, 0.30, footer, size=11.5, color=theme["muted_dark"], align=PP_ALIGN.CENTER)


def add_subject_blueprint_card(
    slide,
    theme: dict,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    kind: str,
    labels: Sequence[str],
    footer: str = "",
):
    """Multi-subject technical schematic card: kind in {'cylinder','parallelogram','triangle','convex_lens','circuit'}."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.9)
    add_text(slide, x + 0.24, y + 0.18, w - 0.48, 0.32, title, size=13, color=theme["gold_bright"], bold=True)

    cx = x + w / 2.0
    cy = y + 0.72 + (h - 1.65) / 2.0
    fw, fh = w * 0.58, h * 0.38
    k = kind.lower().strip()

    if k == "cylinder":
        sh = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(cx - fw * 0.38), Inches(cy - fh / 2), Inches(fw * 0.76), Inches(fh))
        sh.fill.solid()
        sh.fill.fore_color.rgb = theme["dark_panel"]
        sh.line.color.rgb = theme["gold_bright"]
        sh.line.width = Pt(1.5)
    elif k == "parallelogram":
        sh = slide.shapes.add_shape(MSO_SHAPE.PARALLELOGRAM, Inches(cx - fw / 2), Inches(cy - fh / 2), Inches(fw), Inches(fh))
        sh.fill.solid()
        sh.fill.fore_color.rgb = theme["dark_panel"]
        sh.line.color.rgb = theme["gold_bright"]
        sh.line.width = Pt(1.5)
        add_rect(slide, cx - fw * 0.18, cy - fh / 2, 0.022, fh, fill_rgb=theme["accent_bright"])
    elif k == "convex_lens":
        # Optical axis + biconvex lens oval + incident & refracted rays
        add_rect(slide, x + 0.30, cy, w - 0.60, 0.016, fill_rgb=theme["muted_dark"])
        lens = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - 0.22), Inches(cy - fh * 0.55), Inches(0.44), Inches(fh * 1.1))
        lens.fill.solid()
        lens.fill.fore_color.rgb = theme["primary"]
        lens.line.color.rgb = theme["gold_bright"]
        lens.line.width = Pt(1.4)
        add_rect(slide, x + 0.42, cy - fh * 0.32, (w - 0.84) * 0.5, 0.026, fill_rgb=theme["gold_bright"])
        add_rect(slide, cx, cy - fh * 0.16, (w - 0.84) * 0.42, 0.026, fill_rgb=theme["accent_bright"])
    elif k == "circuit":
        add_rect(slide, cx - fw / 2, cy - fh / 2, fw, fh, fill_rgb=None, line_rgb=theme["gold_bright"], line_pt=1.8)
        for off, lbl in [(-fw * 0.22, "R1"), (fw * 0.22, "R2")]:
            box = add_rect(slide, cx + off - 0.38, cy - fh / 2 - 0.16, 0.76, 0.32, fill_rgb=theme["primary"], line_rgb=theme["ink_light"], line_pt=1.0)
            box.text_frame.paragraphs[0].text = lbl
    else:
        sh = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(cx - fw / 2), Inches(cy - fh / 2), Inches(fw), Inches(fh))
        sh.fill.solid()
        sh.fill.fore_color.rgb = theme["dark_panel"]
        sh.line.color.rgb = theme["gold_bright"]
        sh.line.width = Pt(1.5)

    ly = cy + fh / 2 + 0.22
    for i, lbl in enumerate(labels[:3]):
        add_text(slide, x + 0.24, ly + i * 0.28, w - 0.48, 0.26, lbl, size=12, color=theme["ink_light"] if i == 0 else theme["gold_bright"], bold=True, align=PP_ALIGN.CENTER)

    if footer:
        add_rect(slide, x + 0.24, y + h - 0.72, w - 0.48, 0.014, fill_rgb=theme["gold"])
        add_text(slide, x + 0.24, y + h - 0.62, w - 0.48, 0.48, footer, size=11.5, color=theme["muted_dark"], line_spacing=1.25)


# ==============================================================================
# SPECIALIZED SOLID-GEOMETRY VECTOR BUILDERS (Backward-Compatible)
# ==============================================================================

def add_equal_base_height_gauge(slide, theme: dict, x, y, w, h, title: str = "实验前提标尺：先量后倒"):
    """Native editable vector schematic showing equal base diameter (d) and equal height (h) between cone & cylinder."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.8)
    add_text(slide, x + 0.28, y + 0.22, w - 0.56, 0.34, title, size=14, color=theme["gold_bright"], bold=True)

    top_y = y + 1.05
    bot_y = y + h - 1.12
    fig_h = bot_y - top_y
    add_rect(slide, x + 0.42, top_y, w - 0.84, 0.016, fill_rgb=theme["gold_bright"])
    add_rect(slide, x + 0.42, bot_y, w - 0.84, 0.020, fill_rgb=theme["gold_bright"])

    cw = min(1.55, w * 0.28)
    cx1 = x + w * 0.27 - cw / 2
    tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(cx1), Inches(top_y + 0.02), Inches(cw), Inches(fig_h - 0.14))
    tri.fill.solid()
    tri.fill.fore_color.rgb = theme["primary"]
    tri.line.color.rgb = theme["gold_bright"]
    tri.line.width = Pt(1.2)

    oval1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx1), Inches(bot_y - 0.24), Inches(cw), Inches(0.24))
    oval1.fill.solid()
    oval1.fill.fore_color.rgb = theme["dark_panel"]
    oval1.line.color.rgb = theme["gold_bright"]
    oval1.line.width = Pt(1.2)

    cx2 = x + w * 0.67 - cw / 2
    cyl = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(cx2), Inches(top_y + 0.02), Inches(cw), Inches(fig_h - 0.02))
    cyl.fill.solid()
    cyl.fill.fore_color.rgb = theme["dark_panel"]
    cyl.line.color.rgb = theme["gold_bright"]
    cyl.line.width = Pt(1.2)

    gx = x + w - 0.68
    add_rect(slide, gx, top_y, 0.022, fig_h, fill_rgb=theme["accent_bright"])
    add_text(slide, gx - 0.36, top_y + fig_h * 0.36, 0.72, 0.36, "等高 h", size=12, color=theme["accent_bright"], bold=True, align=PP_ALIGN.CENTER)

    add_text(slide, cx1 - 0.15, bot_y + 0.14, cw + 0.30, 0.32, "圆锥 · 底径 d", size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, cx2 - 0.15, bot_y + 0.14, cw + 0.30, 0.32, "圆柱 · 底径 d", size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, x + 0.28, y + h - 0.46, w - 0.56, 0.32, "先拿直尺贴合比底、比高，完全重合才能开始倒沙", size=11.5, color=theme["muted_dark"], align=PP_ALIGN.CENTER)


def add_three_to_one_derivation_graphic(slide, theme: dict, x, y, w, h):
    """Native editable dark-gallery 3-cones -> 3x(1/3) stacked cylinder derivation diagram (zero recycled photos)."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_panel"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.9)
    add_text(slide, x + 0.28, y + 0.20, w - 0.56, 0.34, "守恒推演图解：3 个等底等高圆锥  =  1 个完整圆柱", size=13.5, color=theme["gold_bright"], bold=True)

    cone_w = min(0.95, w * 0.15)
    cone_h = min(1.45, h * 0.38)
    cy = y + 1.05
    gap = 0.20
    start_x = x + 0.36
    labels = ["第 1 锥", "第 2 锥", "第 3 锥"]
    for i in range(3):
        cx = start_x + i * (cone_w + gap)
        tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(cx), Inches(cy), Inches(cone_w), Inches(cone_h))
        tri.fill.solid()
        tri.fill.fore_color.rgb = theme["gold"] if i < 2 else theme["gold_bright"]
        tri.line.color.rgb = theme["ink_light"]
        tri.line.width = Pt(1.0)
        add_text(slide, cx - 0.08, cy + cone_h + 0.12, cone_w + 0.16, 0.32, labels[i], size=12, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, cx - 0.08, cy + cone_h + 0.42, cone_w + 0.16, 0.28, "1/3 V柱", size=11.5, color=theme["gold_bright"], font_name=FONT_NUM, align=PP_ALIGN.CENTER)
        if i < 2:
            add_text(slide, cx + cone_w + 0.01, cy + cone_h * 0.42, 0.18, 0.36, "+", size=16, color=theme["gold_bright"], bold=True, font_name=FONT_NUM, align=PP_ALIGN.CENTER)

    arr_x = start_x + 3 * cone_w + 2 * gap + 0.16
    arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(arr_x), Inches(cy + cone_h * 0.38), Inches(0.46), Inches(0.32))
    arr.fill.solid()
    arr.fill.fore_color.rgb = theme["gold_bright"]
    arr.line.fill.background()

    cyl_x = arr_x + 0.62
    cyl_w = max(1.35, (x + w - 0.36) - cyl_x)
    tier_h = (cone_h + 0.36) / 3.0
    tier_top = cy - 0.16
    tier_meta = [
        ("第 3 次 · 齐口满（3/3）", theme["gold_bright"], theme["dark_bg"]),
        ("第 2 次 · 上升至 2/3", theme["gold"], theme["dark_bg"]),
        ("第 1 次 · 填满底层 1/3", theme["primary"], theme["ink_light"]),
    ]
    for idx, (tlabel, fill_c, txt_c) in enumerate(tier_meta):
        ty = tier_top + idx * (tier_h + 0.05)
        add_rect(slide, cyl_x, ty, cyl_w, tier_h, fill_rgb=fill_c, line_rgb=theme["ink_light"], line_pt=0.9)
        add_text(slide, cyl_x + 0.06, ty + tier_h * 0.22, cyl_w - 0.12, tier_h * 0.62, tlabel, size=11.5, color=txt_c, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    add_text(slide, x + 0.28, y + h - 0.56, w - 0.56, 0.36, "体积守恒：V 圆柱 = 3 × V 圆锥  ⇒  V 圆锥 = 1/3 V 圆柱 = 1/3 S h", size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)


def add_cone_blueprint_card(slide, theme: dict, x, y, w, h, title: str, d_label: str, r_label: str, h_label: str, footer: str):
    """Native architectural technical blueprint diagram for textbook example problems (zero reused AI photos)."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.9)
    add_text(slide, x + 0.24, y + 0.18, w - 0.48, 0.32, title, size=13, color=theme["gold_bright"], bold=True)

    bw = w * 0.66
    bh = h * 0.42
    bx = x + (w - bw) / 2
    by = y + 0.80
    tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(bx), Inches(by), Inches(bw), Inches(bh))
    tri.fill.solid()
    tri.fill.fore_color.rgb = theme["dark_panel"]
    tri.line.color.rgb = theme["gold_bright"]
    tri.line.width = Pt(1.5)

    ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(bx), Inches(by + bh - 0.22), Inches(bw), Inches(0.42))
    ov.fill.solid()
    ov.fill.fore_color.rgb = theme["primary"]
    ov.line.color.rgb = theme["gold_bright"]
    ov.line.width = Pt(1.4)

    cx = bx + bw / 2
    add_rect(slide, cx - 0.012, by + 0.04, 0.024, bh - 0.04, fill_rgb=theme["accent_bright"])
    add_rect(slide, cx, by + bh - 0.02, bw / 2, 0.024, fill_rgb=theme["gold_bright"])

    add_text(slide, cx + 0.08, by + bh * 0.36, 1.45, 0.30, h_label, size=12, color=theme["accent_bright"], bold=True)
    add_text(slide, bx, by + bh + 0.24, bw, 0.28, d_label, size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, bx, by + bh + 0.52, bw, 0.26, r_label, size=11.5, color=theme["gold_bright"], bold=True, align=PP_ALIGN.CENTER)

    add_rect(slide, x + 0.24, y + h - 0.78, w - 0.48, 0.014, fill_rgb=theme["gold"])
    add_text(slide, x + 0.24, y + h - 0.68, w - 0.48, 0.54, footer, size=11.5, color=theme["muted_dark"], line_spacing=1.28)
