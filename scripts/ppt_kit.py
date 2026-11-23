#!/usr/bin/env python3
"""
ppt_kit.py — Reusable 16:9 Museum-Magazine Editable Teaching PPTX Builder (k12-lesson-studio v4.1)

Guarantees:
- 16:9 canvas (13.333 in x 7.5 in) with safe non-overlapping grids
- 4 curated subject palettes (math, chinese, english, science)
- 100% native editable text frames & tables (Seewo / WPS / PowerPoint compatible)
- Offline playable MP4 video slide helper (add_movie + poster frame + 3-step beats)
- Native OOXML slide fade transitions (<p:transition>) & mandatory speaker notes
"""
from __future__ import annotations

import pathlib
from typing import Sequence

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
}


def get_theme(name: str = "math") -> dict:
    return THEMES.get(name.lower(), THEMES["math"])


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
    # Single combined eyebrow textbox to guarantee zero overlap between number and tag
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
    slide.shapes.add_picture(str(img_path), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))
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

    # Gold cinema bezel + offline embedded MP4 via add_movie()
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

    # Right-side 3-step observation beats (zero overlap)
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

    # Bottom right offline playback badge
    add_rect(slide, rx, 5.44, rw, 0.96, fill_rgb=theme["dark_panel"], line_rgb=theme["gold"], line_pt=0.8)
    add_text(slide, rx + 0.16, 5.54, rw - 0.32, 0.32, badge_title, size=13, color=theme["gold_bright"], bold=True)
    add_text(slide, rx + 0.16, 5.88, rw - 0.32, 0.46, badge_desc, size=11.5, color=theme["muted_dark"], line_spacing=1.25)
    set_notes(slide, notes)
    return slide


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


def add_equal_base_height_gauge(slide, theme: dict, x, y, w, h, title: str = "实验前提标尺：先量后倒"):
    """Native editable vector schematic showing equal base diameter (d) and equal height (h) between cone & cylinder."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_bg"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.8)
    add_text(slide, x + 0.28, y + 0.22, w - 0.56, 0.34, title, size=14, color=theme["gold_bright"], bold=True)

    # Top and bottom horizontal alignment gauge lines
    top_y = y + 1.05
    bot_y = y + h - 1.12
    fig_h = bot_y - top_y
    add_rect(slide, x + 0.42, top_y, w - 0.84, 0.016, fill_rgb=theme["gold_bright"])
    add_rect(slide, x + 0.42, bot_y, w - 0.84, 0.020, fill_rgb=theme["gold_bright"])

    # Left: Cone triangle + elliptical base
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

    # Right: Equal-width equal-height Cylinder
    cx2 = x + w * 0.67 - cw / 2
    cyl = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(cx2), Inches(top_y + 0.02), Inches(cw), Inches(fig_h - 0.02))
    cyl.fill.solid()
    cyl.fill.fore_color.rgb = theme["dark_panel"]
    cyl.line.color.rgb = theme["gold_bright"]
    cyl.line.width = Pt(1.2)

    # Vertical height gauge bar on far right
    gx = x + w - 0.68
    add_rect(slide, gx, top_y, 0.022, fig_h, fill_rgb=theme["accent_bright"])
    add_text(slide, gx - 0.36, top_y + fig_h * 0.36, 0.72, 0.36, "等高 h", size=12, color=theme["accent_bright"], bold=True, align=PP_ALIGN.CENTER)

    # Base labels
    add_text(slide, cx1 - 0.15, bot_y + 0.14, cw + 0.30, 0.32, "圆锥 · 底径 d", size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, cx2 - 0.15, bot_y + 0.14, cw + 0.30, 0.32, "圆柱 · 底径 d", size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, x + 0.28, y + h - 0.46, w - 0.56, 0.32, "先拿直尺贴合比底、比高，完全重合才能开始倒沙", size=11.5, color=theme["muted_dark"], align=PP_ALIGN.CENTER)


def add_three_to_one_derivation_graphic(slide, theme: dict, x, y, w, h):
    """Native editable dark-gallery 3-cones -> 3x(1/3) stacked cylinder derivation diagram (zero recycled photos)."""
    add_card(slide, x, y, w, h, fill_rgb=theme["dark_panel"], accent_top_rgb=theme["gold_bright"], border_rgb=theme["gold"], border_pt=0.9)
    add_text(slide, x + 0.28, y + 0.20, w - 0.56, 0.34, "守恒推演图解：3 个等底等高圆锥  =  1 个完整圆柱", size=13.5, color=theme["gold_bright"], bold=True)

    # Left half: 3 aligned equal golden cones stacked in a clean vertical or horizontal row
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

    # Center equals arrow
    arr_x = start_x + 3 * cone_w + 2 * gap + 0.16
    arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(arr_x), Inches(cy + cone_h * 0.38), Inches(0.46), Inches(0.32))
    arr.fill.solid()
    arr.fill.fore_color.rgb = theme["gold_bright"]
    arr.line.fill.background()

    # Right side: 3-tier stacked proportional cylinder (1/3 + 1/3 + 1/3)
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

    # Blueprint triangle cross-section
    bw = w * 0.66
    bh = h * 0.42
    bx = x + (w - bw) / 2
    by = y + 0.80
    tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(bx), Inches(by), Inches(bw), Inches(bh))
    tri.fill.solid()
    tri.fill.fore_color.rgb = theme["dark_panel"]
    tri.line.color.rgb = theme["gold_bright"]
    tri.line.width = Pt(1.5)

    # Base ellipse
    ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(bx), Inches(by + bh - 0.22), Inches(bw), Inches(0.42))
    ov.fill.solid()
    ov.fill.fore_color.rgb = theme["primary"]
    ov.line.color.rgb = theme["gold_bright"]
    ov.line.width = Pt(1.4)

    # Center vertical height line
    cx = bx + bw / 2
    add_rect(slide, cx - 0.012, by + 0.04, 0.024, bh - 0.04, fill_rgb=theme["accent_bright"])
    # Radius bar from center to right edge
    add_rect(slide, cx, by + bh - 0.02, bw / 2, 0.024, fill_rgb=theme["gold_bright"])

    # Clean non-overlapping dimension callouts (radius placed cleanly below diameter to avoid overlapping base ellipse)
    add_text(slide, cx + 0.08, by + bh * 0.36, 1.45, 0.30, h_label, size=12, color=theme["accent_bright"], bold=True)
    add_text(slide, bx, by + bh + 0.24, bw, 0.28, d_label, size=12.5, color=theme["ink_light"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, bx, by + bh + 0.52, bw, 0.26, r_label, size=11.5, color=theme["gold_bright"], bold=True, align=PP_ALIGN.CENTER)

    add_rect(slide, x + 0.24, y + h - 0.78, w - 0.48, 0.014, fill_rgb=theme["gold"])
    add_text(slide, x + 0.24, y + h - 0.68, w - 0.48, 0.54, footer, size=11.5, color=theme["muted_dark"], line_spacing=1.28)
