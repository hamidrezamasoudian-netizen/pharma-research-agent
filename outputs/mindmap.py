"""
mindmap.py – مایند مپ با فونت فارسی خوانا و جزئیات
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def reshape_fa(text: str) -> str:
        if not text:
            return ""
        return get_display(arabic_reshaper.reshape(str(text)))
except Exception:
    def reshape_fa(text: str) -> str:
        return str(text or "")

COLORS = {
    "bg": (248, 250, 252),
    "center": (30, 64, 175),
    "center_text": (255, 255, 255),
    "level1": (37, 99, 235),
    "level1_text": (255, 255, 255),
    "level2": (226, 232, 240),
    "level2_text": (15, 23, 42),
    "line": (147, 197, 253),
    "shadow": (203, 213, 225),
}

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_font(size: int, bold: bool = False):
    # اولویت با فونت فارسی واقعی
    candidates = [
        Path("fonts/Vazirmatn-Bold.ttf") if bold else Path("fonts/Vazirmatn-Regular.ttf"),
        Path("fonts/Vazirmatn-Regular.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        probe = reshape_fa(test)
        bbox = draw.textbbox((0, 0), probe, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [str(text)]


def _draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle((x1 + 2, y1 + 2, x2 + 2, y2 + 2), radius=radius, fill=COLORS["shadow"])
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _draw_node(draw, center, text, font, fill, text_color, max_width=220, padding=10):
    lines_raw = _wrap_text(text, font, max_width - 2 * padding, draw)
    lines = [reshape_fa(x) for x in lines_raw]
    line_heights = []
    max_line_w = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_heights.append(max(h, 12))
        max_line_w = max(max_line_w, w)

    total_h = sum(line_heights) + (len(lines) - 1) * 3 + 2 * padding
    total_w = max(max_line_w + 2 * padding, 70)
    x, y = center
    box = (x - total_w // 2, y - total_h // 2, x + total_w // 2, y + total_h // 2)
    _draw_rounded_rect(draw, box, 14, fill)

    current_y = y - total_h // 2 + padding
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, current_y), line, font=font, fill=text_color)
        current_y += line_heights[i] + 3
    return total_w, total_h


def build_mindmap_structure(topic: str, research_data: dict | None = None) -> dict[str, Any]:
    data = research_data or {}
    key_points = data.get("key_points") or []

    if not key_points or len(key_points) < 2:
        key_points = [
            {"title": "مکانیسم", "children": ["مسیر اثر", "شروع اثر", "متابولیسم"]},
            {"title": "مصرف", "children": ["اندیکاسیون", "محدودیت", "گروه خاص"]},
            {"title": "عوارض", "children": ["شایع", "جدی", "هشدار"]},
            {"title": "تداخلات", "children": ["دارویی", "غذایی", "احتیاط"]},
            {"title": "پایش", "children": ["دوز", "آزمایش", "آموزش"]},
        ]

    normalized = []
    for kp in key_points[:5]:
        if isinstance(kp, dict):
            title = str(kp.get("title") or "شاخه")[:28]
            children = [str(c)[:26] for c in (kp.get("children") or []) if str(c).strip()][:3]
            if not children:
                children = ["جزئیات مقاله"]
            normalized.append({"title": title, "children": children})
        else:
            normalized.append({"title": str(kp)[:28], "children": ["جزئیات"]})

    center = topic if len(topic) <= 36 else topic[:33] + "…"
    return {"center": center, "branches": normalized}


def generate_mindmap_image(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
) -> str:
    structure = build_mindmap_structure(topic, research_data)
    branches = structure["branches"]
    center_text = structure["center"]

    width, height = 1700, 1300
    img = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # اندازه فونت کوچک‌تر و خوانا (نه درشت)
    font_center = _load_font(20, bold=True)
    font_l1 = _load_font(15, bold=True)
    font_l2 = _load_font(12, bold=False)
    font_footer = _load_font(11)

    cx, cy = width // 2, height // 2
    _draw_node(draw, (cx, cy), center_text, font_center, COLORS["center"], COLORS["center_text"], 300, 12)

    n = max(len(branches), 1)
    radius = 380

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n) - math.pi / 2
        bx = int(cx + radius * math.cos(angle))
        by = int(cy + radius * math.sin(angle))
        draw.line([(cx, cy), (bx, by)], fill=COLORS["line"], width=3)

        title = branch.get("title", f"شاخه {i+1}")
        children = branch.get("children") or []
        _draw_node(draw, (bx, by), title, font_l1, COLORS["level1"], COLORS["level1_text"], 190, 8)

        if children:
            m = len(children)
            child_radius = 155
            spread = min(0.85, 0.32 + 0.12 * m)
            for j, child in enumerate(children):
                child_angle = angle if m == 1 else angle - spread / 2 + (spread * j / (m - 1))
                cx2 = int(bx + child_radius * math.cos(child_angle))
                cy2 = int(by + child_radius * math.sin(child_angle))
                cx2 = max(80, min(width - 80, cx2))
                cy2 = max(50, min(height - 70, cy2))
                draw.line([(bx, by), (cx2, cy2)], fill=COLORS["line"], width=2)
                _draw_node(draw, (cx2, cy2), str(child), font_l2, COLORS["level2"], COLORS["level2_text"], 160, 6)

    footer = reshape_fa("Pharma Research Agent | مایند مپ تحقیق دارویی")
    bbox = draw.textbbox((0, 0), footer, font=font_footer)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 32), footer, font=font_footer, fill=(100, 116, 139))

    if not output_name:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic[:40])
        output_name = f"mindmap_{safe}.png"

    out_path = OUTPUT_DIR / output_name
    img.save(out_path, "PNG")
    print(f"[MINDMAP] → {out_path}")
    return str(out_path)
