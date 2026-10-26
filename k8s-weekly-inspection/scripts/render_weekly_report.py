#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 template/design-language.yaml 把维护周报 Markdown 渲染为 PDF。

样式以 2026-09-21 / 09-30 / 10-12 交付 PDF 为基准；改视觉只改 YAML，不改本脚本里的魔法数。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "template" / "design-language.yaml"


def load_design(path: Path = DESIGN_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def hex_color(value: str) -> colors.Color:
    return colors.HexColor(value)


def resolve_color(design: dict, key_or_hex: str) -> colors.Color:
    palette = design["colors"]
    if key_or_hex in palette:
        return hex_color(palette[key_or_hex])
    if key_or_hex.startswith("#"):
        return hex_color(key_or_hex)
    raise KeyError(f"unknown color ref: {key_or_hex}")


def register_fonts(design: dict) -> tuple[str, str]:
    base = design["fonts"]["base"]
    bold = design["fonts"]["bold"]
    pdfmetrics.registerFont(
        TTFont(base["register_as"], base["path"], subfontIndex=base.get("subfont_index", 0))
    )
    try:
        pdfmetrics.registerFont(
            TTFont(bold["register_as"], bold["path"], subfontIndex=bold.get("subfont_index", 0))
        )
        return base["register_as"], bold["register_as"]
    except Exception:
        return base["register_as"], base["register_as"]


def make_style(name: str, spec: dict, font_base: str, font_bold: str, color: colors.Color) -> ParagraphStyle:
    return ParagraphStyle(
        name,
        fontName=font_bold if spec.get("bold") else font_base,
        fontSize=spec["size"],
        leading=spec["leading"],
        textColor=color,
        spaceBefore=spec.get("space_before", 2),
        spaceAfter=spec.get("space_after", 4),
        alignment=TA_LEFT,
        leftIndent=spec.get("left_indent", 0),
    )


def build_styles(design: dict, font_base: str, font_bold: str) -> dict:
    c = design["colors"]
    t = design["typography"]
    return {
        "title": make_style("t", t["title"], font_base, font_bold, hex_color(c["title"])),
        "h1": make_style("h1", t["h1"], font_base, font_bold, hex_color(c["h1"])),
        "h2": make_style("h2", t["h2"], font_base, font_bold, hex_color(c["h2"])),
        "h3": make_style("h3", t["h3"], font_base, font_bold, hex_color(c["h3"])),
        "body": make_style("p", t["body"], font_base, font_bold, hex_color(c["body"])),
        "meta": make_style("d", t["meta"], font_base, font_bold, hex_color(c["meta"])),
        "list": make_style("li", t["list"], font_base, font_bold, hex_color(c["body"])),
        "quote": make_style("bq", t["quote"], font_base, font_bold, hex_color(c["quote"])),
        "th": make_style("th", t["th"], font_base, font_bold, hex_color(c["table_header_fg"])),
        "td": make_style("td", t["td"], font_base, font_bold, hex_color(c["body"])),
    }


def glyph_map(design: dict) -> dict[str, str]:
    out = {}
    for src, tpl in design.get("glyph_fallback", {}).items():
        out[src] = tpl.format(**design["colors"])
    return out


def esc(text: str, font_base: str, glyphs: dict[str, str]) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", rf'<font face="{font_base}">\1</font>', text)
    text = text.replace("\u2248", "~")
    # longer keys first so ⚠️ wins over ⚠
    for ch in sorted(glyphs.keys(), key=len, reverse=True):
        text = text.replace(ch, glyphs[ch])
    return text


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def make_table(rows: list[list[str]], design: dict, styles: dict, font_base: str, glyphs: dict) -> Table:
    body = []
    for index, row in enumerate(rows):
        cell_style = styles["th"] if index == 0 else styles["td"]
        body.append([Paragraph(esc(cell, font_base, glyphs), cell_style) for cell in row])
    width = max(len(row) for row in rows)
    for row in body:
        while len(row) < width:
            row.append(Paragraph("", styles["td"]))
    tbl_cfg = design["table"]
    table = Table(body, repeatRows=1 if tbl_cfg.get("repeat_header", True) else 0)
    pad = tbl_cfg["padding"]
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), resolve_color(design, tbl_cfg["header_background"])),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            resolve_color(design, tbl_cfg["stripe_background"]),
        ]),
        ("GRID", (0, 0), (-1, -1), tbl_cfg["grid_width"], resolve_color(design, tbl_cfg["grid_color"])),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), pad["left"]),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad["right"]),
        ("TOPPADDING", (0, 0), (-1, -1), pad["top"]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad["bottom"]),
    ]))
    return table


def build(src: str, out: str, design_path: Path = DESIGN_PATH) -> None:
    design = load_design(design_path)
    font_base, font_bold = register_fonts(design)
    styles = build_styles(design, font_base, font_bold)
    glyphs = glyph_map(design)
    bullet = design.get("list", {}).get("bullet", "•")
    tbl_cfg = design["table"]
    hr_cfg = design["hr"]
    margins = design["page"]["margins_mm"]

    lines = open(src, encoding="utf-8").read().split("\n")
    story = []
    index = 0
    first_h1_done = False
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and set(lines[index + 1].strip()) <= set("|-: ")
        ):
            rows = [split_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_row(lines[index]))
                index += 1
            story.append(Spacer(1, tbl_cfg.get("spacer_before", 3)))
            story.append(make_table(rows, design, styles, font_base, glyphs))
            story.append(Spacer(1, tbl_cfg.get("spacer_after", 6)))
            continue
        if stripped.startswith("# "):
            style = styles["title"] if not first_h1_done else styles["h1"]
            first_h1_done = True
            story.append(Paragraph(esc(stripped[2:], font_base, glyphs), style))
        elif stripped.startswith("## "):
            story.append(Paragraph(esc(stripped[3:], font_base, glyphs), styles["h1"]))
        elif stripped.startswith("### "):
            story.append(Paragraph(esc(stripped[4:], font_base, glyphs), styles["h2"]))
        elif stripped.startswith("#### "):
            story.append(Paragraph(esc(stripped[5:], font_base, glyphs), styles["h3"]))
        elif stripped.startswith("> "):
            story.append(Paragraph(esc(stripped[2:], font_base, glyphs), styles["quote"]))
        elif stripped.startswith("- "):
            story.append(Paragraph(bullet + " " + esc(stripped[2:], font_base, glyphs), styles["list"]))
        elif stripped.startswith("---"):
            story.append(HRFlowable(
                width="100%",
                thickness=hr_cfg["thickness"],
                color=resolve_color(design, hr_cfg["color"]),
                spaceBefore=hr_cfg.get("space_before", 4),
                spaceAfter=hr_cfg.get("space_after", 6),
            ))
        else:
            story.append(Paragraph(esc(stripped, font_base, glyphs), styles["body"]))
        index += 1

    title = "维护周报"
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        topMargin=margins["top"] * mm,
        bottomMargin=margins["bottom"] * mm,
        leftMargin=margins["left"] * mm,
        rightMargin=margins["right"] * mm,
        title=title,
        author=design["page"].get("author", "unix"),
    )
    doc.build(story)
    print("written", out)
    print("design", design_path)


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print(
            "usage: render_weekly_report.py INPUT.md OUTPUT.pdf [design-language.yaml]",
            file=sys.stderr,
        )
        return 2
    design = Path(sys.argv[3]) if len(sys.argv) == 4 else DESIGN_PATH
    build(sys.argv[1], sys.argv[2], design)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
