"""
mindmap.py – مایند مپ تصویری با متن فارسی صحیح و جزئیات تحقیق
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
    "level2": (219, 234, 254),
    "level2_text": (30, 58, 138),
    "line": (147, 197, 253),
    "shadow": (203, 213, 225),
}

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += [
            Path("fonts/Vazirmatn-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
    candidates += [
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
    # برای فارسی بعد از reshape فاصله‌ها ممکن است عجیب شوند؛ روی متن خام wrap می‌کنیم سپس reshape
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        # اندازه با reshape تقریبی
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
    draw.rounded_rectangle((x1 + 3, y1 + 3, x2 + 3, y2 + 3), radius=radius, fill=COLORS["shadow"])
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _draw_node(draw, center, text, font, fill, text_color, max_width=240, padding=12):
    lines_raw = _wrap_text(text, font, max_width - 2 * padding, draw)
    lines = [reshape_fa(x) for x in lines_raw]
    line_heights = []
    max_line_w = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_heights.append(max(h, 14))
        max_line_w = max(max_line_w, w)

    total_h = sum(line_heights) + (len(lines) - 1) * 4 + 2 * padding
    total_w = max(max_line_w + 2 * padding, 80)
    x, y = center
    box = (x - total_w // 2, y - total_h // 2, x + total_w // 2, y + total_h // 2)
    _draw_rounded_rect(draw, box, 16, fill)

    current_y = y - total_h // 2 + padding
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, current_y), line, font=font, fill=text_color)
        current_y += line_heights[i] + 4
    return total_w, total_h


def build_mindmap_structure(topic: str, research_data: dict | None = None) -> dict[str, Any]:
    data = research_data or {}
    key_points = data.get("key_points") or []

    # اگر تحقیق خالی/ضعیف بود، شاخه‌های استاندارد غنی بساز
    if not key_points or len(key_points) < 2:
        key_points = [
            {"title": "مکانیسم و فارماکولوژی", "children": ["مسیر اثر", "شروع و مدت اثر", "متابولیسم"]},
            {"title": "موارد مصرف", "children": ["اندیکاسیون اصلی", "موارد خاص", "محدودیت‌ها"]},
            {"title": "عوارض شایع و جدی", "children": ["عوارض شایع", "عوارض جدی", "علائم هشدار"]},
            {"title": "تداخلات مهم", "children": ["تداخل دارویی", "تداخل غذایی", "نکته بالینی"]},
            {"title": "نکات مصرف و پایش", "children": ["دوز", "پایش بیمار", "آموزش بیمار"]},
        ]

    # اگر children خالی بود پر کن
    normalized = []
    for kp in key_points[:6]:
        if isinstance(kp, dict):
            title = str(kp.get("title") or "شاخه")
            children = [str(c) for c in (kp.get("children") or []) if str(c).strip()]
            if not children:
                children = ["جزئیات در مقاله", "نکته بالینی"]
            normalized.append({"title": title[:40], "children": children[:4]})
        else:
            normalized.append({"title": str(kp)[:40], "children": ["جزئیات در مقاله"]})

    center = topic if len(topic) <= 48 else topic[:45] + "…"
    return {"center": center, "branches": normalized}


def generate_mindmap_image(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
) -> str:
    structure = build_mindmap_structure(topic, research_data)
    branches = structure["branches"]
    center_text = structure["center"]

    width, height = 1800, 1400
    img = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    font_center = _load_font(26, bold=True)
    font_l1 = _load_font(18, bold=True)
    font_l2 = _load_font(14)
    font_footer = _load_font(13)

    cx, cy = width // 2, height // 2
    _draw_node(draw, (cx, cy), center_text, font_center, COLORS["center"], COLORS["center_text"], 360, 16)

    n = max(len(branches), 1)
    radius = 420

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n) - math.pi / 2
        bx = int(cx + radius * math.cos(angle))
        by = int(cy + radius * math.sin(angle))
        draw.line([(cx, cy), (bx, by)], fill=COLORS["line"], width=4)

        title = branch.get("title", f"شاخه {i+1}")
        children = branch.get("children") or []
        _draw_node(draw, (bx, by), title, font_l1, COLORS["level1"], COLORS["level1_text"], 220, 10)

        if children:
            m = len(children)
            child_radius = 175
            spread = min(0.9, 0.35 + 0.12 * m)
            for j, child in enumerate(children):
                if m == 1:
                    child_angle = angle
                else:
                    child_angle = angle - spread / 2 + (spread * j / (m - 1))
                cx2 = int(bx + child_radius * math.cos(child_angle))
                cy2 = int(by + child_radius * math.sin(child_angle))
                # جلوگیری از خروج از کادر
                cx2 = max(90, min(width - 90, cx2))
                cy2 = max(60, min(height - 80, cy2))
                draw.line([(bx, by), (cx2, cy2)], fill=COLORS["line"], width=2)
                _draw_node(draw, (cx2, cy2), str(child), font_l2, COLORS["level2"], COLORS["level2_text"], 180, 8)

    footer = reshape_fa("Pharma Research Agent  |  مایند مپ تحقیق دارویی")
    bbox = draw.textbbox((0, 0), footer, font=font_footer)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 36), footer, font=font_footer, fill=(100, 116, 139))

    if not output_name:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic[:40])
        output_name = f"mindmap_{safe}.png"

    out_path = OUTPUT_DIR / output_name
    img.save(out_path, "PNG")
    print(f"[MINDMAP] → {out_path}")
    return str(out_path)
