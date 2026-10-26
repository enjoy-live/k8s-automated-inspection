#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 template/design-language.yaml 把维护周报 Markdown 渲染为 PDF。

样式以 2026-09-21 / 09-30 / 10-12 交付 PDF 为基线，并叠加 YAML 里的强调规则：
本周重点红色有序列表、严重标题与核心行红字、警告行和异常/复发行整行红字加浅红底。
改视觉或判定词只改 YAML，不在本脚本里另写色值或关键词。
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

DEFAULT_RULES = {
    "highlight_label": "本周重点",
    "critical_marker": "【严重】",
    "warning_line_marker": "【警告】",
    "warning_tokens": ["警告", "warning"],
    "critical_tokens": ["严重", "critical"],
    "core_prefixes": ["现象", "结论", "影响"],
    "alert_terms": ["异常", "复发"],
    "alert_negations": [
        "未发现异常",
        "没有发现异常",
        "没有出现异常",
        "未出现异常",
        "不存在异常",
        "未见异常",
        "没有异常",
        "无异常",
        "零异常",
        "未出现复发",
        "没有复发",
        "不存在复发",
        "未见复发",
        "无复发",
        "未复发",
        "不再复发",
    ],
}


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


def rules_of(design: dict) -> dict:
    merged = dict(DEFAULT_RULES)
    custom = design.get("emphasis_rules") or {}
    merged.update(custom)
    return merged


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


def recolor(style: ParagraphStyle, name: str, color: colors.Color) -> ParagraphStyle:
    return ParagraphStyle(name, parent=style, textColor=color)


def build_styles(design: dict, font_base: str, font_bold: str) -> dict:
    palette = design["colors"]
    typo = design["typography"]
    emphasis = hex_color(palette["emphasis"])
    alert = hex_color(palette["row_alert_fg"])
    styles = {
        "title": make_style("t", typo["title"], font_base, font_bold, hex_color(palette["title"])),
        "h1": make_style("h1", typo["h1"], font_base, font_bold, hex_color(palette["h1"])),
        "h2": make_style("h2", typo["h2"], font_base, font_bold, hex_color(palette["h2"])),
        "h3": make_style("h3", typo["h3"], font_base, font_bold, hex_color(palette["h3"])),
        "body": make_style("p", typo["body"], font_base, font_bold, hex_color(palette["body"])),
        "meta": make_style("d", typo["meta"], font_base, font_bold, hex_color(palette["meta"])),
        "list": make_style("li", typo["list"], font_base, font_bold, hex_color(palette["body"])),
        "quote": make_style("bq", typo["quote"], font_base, font_bold, hex_color(palette["quote"])),
        "highlight_title": make_style(
            "hlt", typo["highlight_title"], font_base, font_bold, emphasis
        ),
        "highlight": make_style("hl", typo["highlight"], font_base, font_bold, emphasis),
        "th": make_style("th", typo["th"], font_base, font_bold, hex_color(palette["table_header_fg"])),
        "td": make_style("td", typo["td"], font_base, font_bold, hex_color(palette["body"])),
    }
    styles["h1_alert"] = recolor(styles["h1"], "h1-alert", emphasis)
    styles["h2_alert"] = recolor(styles["h2"], "h2-alert", emphasis)
    styles["h3_alert"] = recolor(styles["h3"], "h3-alert", emphasis)
    styles["body_alert"] = recolor(styles["body"], "p-alert", alert)
    styles["body_core"] = recolor(styles["body"], "p-core", emphasis)
    styles["list_alert"] = recolor(styles["list"], "li-alert", alert)
    styles["list_core"] = recolor(styles["list"], "li-core", emphasis)
    styles["quote_alert"] = recolor(styles["quote"], "bq-alert", alert)
    styles["td_core"] = recolor(styles["td"], "td-core", emphasis)
    styles["td_full"] = recolor(styles["td"], "td-full", alert)
    return styles


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


def alert_hit(text: str, rules: dict) -> bool:
    cleaned = text
    negations = sorted(rules.get("alert_negations") or [], key=len, reverse=True)
    for phrase in negations:
        cleaned = cleaned.replace(phrase, "")
    return any(term and term in cleaned for term in rules.get("alert_terms") or [])


def cell_token(cell: str) -> str:
    token = re.sub(r"[*`]", "", cell).strip()
    token = token.strip("[]【】()（）").strip()
    return token.lower()


def row_kind(cells: list[str], rules: dict) -> str:
    if alert_hit(" ".join(cells), rules):
        return "full"
    warning = {item.lower() for item in rules.get("warning_tokens") or []}
    critical = {item.lower() for item in rules.get("critical_tokens") or []}
    tokens = [cell_token(cell) for cell in cells]
    if any(token in warning for token in tokens):
        return "full"
    if any(token in critical for token in tokens):
        return "core"
    return ""


def make_table(rows: list[list[str]], design: dict, styles: dict, font_base: str, glyphs: dict) -> Table:
    rules = rules_of(design)
    kinds = [""] + [row_kind(row, rules) for row in rows[1:]]
    body = []
    for index, row in enumerate(rows):
        if index == 0:
            cell_style = styles["th"]
        elif kinds[index] == "full":
            cell_style = styles["td_full"]
        elif kinds[index] == "core":
            cell_style = styles["td_core"]
        else:
            cell_style = styles["td"]
        body.append([Paragraph(esc(cell, font_base, glyphs), cell_style) for cell in row])
    width = max(len(row) for row in rows)
    for row in body:
        while len(row) < width:
            row.append(Paragraph("", styles["td"]))
    tbl_cfg = design["table"]
    table = Table(body, repeatRows=1 if tbl_cfg.get("repeat_header", True) else 0)
    pad = tbl_cfg["padding"]
    commands = [
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
    ]
    alert_bg = hex_color(design["colors"]["row_alert_bg"])
    for index, kind in enumerate(kinds):
        if kind == "full":
            commands.append(("BACKGROUND", (0, index), (-1, index), alert_bg))
    table.setStyle(TableStyle(commands))
    return table


def quote_body(stripped: str) -> str | None:
    if not stripped.startswith(">"):
        return None
    return stripped[1:].strip()


def highlight_rest(stripped: str, rules: dict) -> str | None:
    label = rules.get("highlight_label") or "本周重点"
    body = quote_body(stripped)
    quoted = body is not None
    if body is None:
        body = stripped
    match = re.match(rf"^(?:\*\*)?{re.escape(label)}[：:](?:\*\*)?\s*(.*)$", body)
    if not match:
        return None
    if quoted or stripped.startswith(label) or stripped.startswith(f"**{label}"):
        return match.group(1).strip()
    return None


def plain_text(text: str) -> str:
    visible = text.strip()
    visible = re.sub(r"^#+\s+", "", visible)
    visible = re.sub(r"^\d+\.\s+", "", visible)
    visible = re.sub(r"^[-*]\s+", "", visible)
    visible = re.sub(r"\*+", "", visible).strip()
    return visible


def is_core_line(text: str, rules: dict) -> bool:
    visible = plain_text(text)
    prefixes = rules.get("core_prefixes") or []
    return any(visible.startswith(prefix + "：") or visible.startswith(prefix + ":") for prefix in prefixes)


def is_warning_line(text: str, rules: dict) -> bool:
    if text.strip().startswith("#"):
        return False
    marker = rules.get("warning_line_marker") or "【警告】"
    visible = plain_text(text)
    if marker and marker in text:
        return True
    return visible.startswith("警告：") or visible.startswith("警告:")


def text_role(text: str, in_critical: bool, rules: dict) -> str:
    if alert_hit(text, rules) or is_warning_line(text, rules):
        return "alert"
    if in_critical and is_core_line(text, rules):
        return "core"
    return "normal"


def heading_is_alert(stripped: str, rules: dict) -> bool:
    marker = rules.get("critical_marker") or "【严重】"
    return marker in stripped or alert_hit(stripped, rules)


def parse_ordered_item(text: str, counter: int) -> tuple[int, str]:
    match = re.match(r"^(\d+)\.\s+(.*)$", text.strip())
    if match:
        return int(match.group(1)), match.group(2).strip()
    match = re.match(r"^[-*]\s+(.*)$", text.strip())
    if match:
        return counter + 1, match.group(1).strip()
    return counter + 1, text.strip()


def indented(style: ParagraphStyle, spaces: int, cache: dict) -> ParagraphStyle:
    if spaces <= 0:
        return style
    key = (style.name, spaces)
    if key not in cache:
        cache[key] = ParagraphStyle(
            f"{style.name}-ind{spaces}",
            parent=style,
            leftIndent=(style.leftIndent or 0) + (spaces // 2) * 12,
        )
    return cache[key]


def build(src: str, out: str, design_path: Path = DESIGN_PATH) -> None:
    design = load_design(design_path)
    rules = rules_of(design)
    font_base, font_bold = register_fonts(design)
    styles = build_styles(design, font_base, font_bold)
    glyphs = glyph_map(design)
    bullet = design.get("list", {}).get("bullet", "•")
    tbl_cfg = design["table"]
    hr_cfg = design["hr"]
    margins = design["page"]["margins_mm"]
    indent_cache: dict = {}

    lines = open(src, encoding="utf-8").read().split("\n")
    story = []
    index = 0
    first_h1_done = False
    in_critical = False
    in_highlight = False
    highlight_n = 0
    allow_bare_highlight = False

    def add_highlight_item(text: str) -> None:
        nonlocal highlight_n
        number, body = parse_ordered_item(text, highlight_n)
        highlight_n = number
        story.append(Paragraph(f"{number}. " + esc(body, font_base, glyphs), styles["highlight"]))

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            if in_highlight:
                allow_bare_highlight = False
            index += 1
            continue

        if (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and set(lines[index + 1].strip()) <= set("|-: ")
        ):
            in_highlight = False
            rows = [split_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_row(lines[index]))
                index += 1
            story.append(Spacer(1, tbl_cfg.get("spacer_before", 3)))
            story.append(make_table(rows, design, styles, font_base, glyphs))
            story.append(Spacer(1, tbl_cfg.get("spacer_after", 6)))
            continue

        if in_highlight:
            body = quote_body(stripped)
            ordered = re.match(r"^(\d+)\.\s+\S", stripped)
            if body is not None:
                if body == "":
                    index += 1
                    continue
                if highlight_rest(stripped, rules) is not None:
                    in_highlight = False
                else:
                    add_highlight_item(body)
                    allow_bare_highlight = True
                    index += 1
                    continue
            elif ordered and allow_bare_highlight:
                add_highlight_item(stripped)
                index += 1
                continue
            else:
                in_highlight = False

        label_rest = highlight_rest(stripped, rules)
        if label_rest is not None:
            in_highlight = True
            highlight_n = 0
            allow_bare_highlight = True
            story.append(Paragraph(esc(rules.get("highlight_label") or "本周重点", font_base, glyphs), styles["highlight_title"]))
            if label_rest:
                add_highlight_item(label_rest)
            index += 1
            continue

        if stripped.startswith("# "):
            in_critical = (rules.get("critical_marker") or "【严重】") in stripped
            style = styles["title"] if not first_h1_done else styles["h1_alert" if heading_is_alert(stripped, rules) else "h1"]
            first_h1_done = True
            story.append(Paragraph(esc(stripped[2:], font_base, glyphs), style))
        elif stripped.startswith("## "):
            in_critical = (rules.get("critical_marker") or "【严重】") in stripped
            style = styles["h1_alert"] if heading_is_alert(stripped, rules) else styles["h1"]
            story.append(Paragraph(esc(stripped[3:], font_base, glyphs), style))
        elif stripped.startswith("### "):
            in_critical = (rules.get("critical_marker") or "【严重】") in stripped
            style = styles["h2_alert"] if heading_is_alert(stripped, rules) else styles["h2"]
            story.append(Paragraph(esc(stripped[4:], font_base, glyphs), style))
        elif stripped.startswith("#### "):
            in_critical = (rules.get("critical_marker") or "【严重】") in stripped
            style = styles["h3_alert"] if heading_is_alert(stripped, rules) else styles["h3"]
            story.append(Paragraph(esc(stripped[5:], font_base, glyphs), style))
        elif quote_body(stripped) is not None:
            body = quote_body(stripped) or ""
            role = text_role(body, in_critical, rules)
            style = styles["quote_alert"] if role == "alert" else styles["quote"]
            story.append(Paragraph(esc(body, font_base, glyphs), style))
        else:
            ordered = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line.rstrip("\n"))
            bullet_line = re.match(r"^(\s*)[-*]\s+(.*)$", line.rstrip("\n"))
            if ordered:
                spaces = len(ordered.group(1))
                role = text_role(ordered.group(3), in_critical, rules)
                base = styles[{"alert": "list_alert", "core": "list_core"}.get(role, "list")]
                story.append(Paragraph(
                    f"{ordered.group(2)}. " + esc(ordered.group(3).strip(), font_base, glyphs),
                    indented(base, spaces, indent_cache),
                ))
            elif bullet_line:
                spaces = len(bullet_line.group(1))
                role = text_role(bullet_line.group(2), in_critical, rules)
                base = styles[{"alert": "list_alert", "core": "list_core"}.get(role, "list")]
                story.append(Paragraph(
                    bullet + " " + esc(bullet_line.group(2).strip(), font_base, glyphs),
                    indented(base, spaces, indent_cache),
                ))
            elif stripped.startswith("---"):
                story.append(HRFlowable(
                    width="100%",
                    thickness=hr_cfg["thickness"],
                    color=resolve_color(design, hr_cfg["color"]),
                    spaceBefore=hr_cfg.get("space_before", 4),
                    spaceAfter=hr_cfg.get("space_after", 6),
                ))
            else:
                role = text_role(stripped, in_critical, rules)
                style = styles[{"alert": "body_alert", "core": "body_core"}.get(role, "body")]
                story.append(Paragraph(esc(stripped, font_base, glyphs), style))
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
