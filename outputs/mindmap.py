"""
mindmap.py – تولید مایند مپ تصویری برای موضوعات دارویی

این ماژول یک مایند مپ سلسله‌مراتبی تمیز با Pillow می‌سازد.
در آینده می‌تواند به Visualizer Agent مستقل تبدیل شود.
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

# رنگ‌های حرفه‌ای و خوانا
COLORS = {
    "bg": (248, 250, 252),          # پس‌زمینه روشن
    "center": (30, 64, 175),        # آبی تیره مرکزی
    "center_text": (255, 255, 255),
    "level1": (37, 99, 235),        # آبی اصلی
    "level1_text": (255, 255, 255),
    "level2": (219, 234, 254),      # آبی خیلی روشن
    "level2_text": (30, 58, 138),
    "line": (147, 197, 253),
    "shadow": (203, 213, 225),
}

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """سعی می‌کند فونت فارسی یا پیش‌فرض سیستم را پیدا کند."""
    candidates = []
    if bold:
        candidates += [
            Path("fonts/Vazirmatn-Bold.ttf"),
            Path("/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
    candidates += [
        Path("fonts/Vazirmatn-Regular.ttf"),
        Path("/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """متن را بر اساس عرض پیکسلی می‌شکند."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [text]


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill, outline=None, width=2):
    """مستطیل گرد با سایه ملایم."""
    x1, y1, x2, y2 = xy
    # سایه
    draw.rounded_rectangle(
        (x1 + 3, y1 + 3, x2 + 3, y2 + 3),
        radius=radius,
        fill=COLORS["shadow"],
    )
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_node(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    text: str,
    font,
    fill,
    text_color,
    max_width: int = 220,
    padding: int = 14,
):
    """یک گره متنی گرد یا مستطیل‌گرد رسم می‌کند و اندازه واقعی آن را برمی‌گرداند."""
    lines = _wrap_text(text, font, max_width - 2 * padding, draw)
    line_heights = []
    max_line_w = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        max_line_w = max(max_line_w, w)

    total_h = sum(line_heights) + (len(lines) - 1) * 6 + 2 * padding
    total_w = max_line_w + 2 * padding

    x, y = center
    box = (x - total_w // 2, y - total_h // 2, x + total_w // 2, y + total_h // 2)
    _draw_rounded_rect(draw, box, radius=18, fill=fill, outline=None)

    # متن
    current_y = y - total_h // 2 + padding
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, current_y), line, font=font, fill=text_color)
        current_y += line_heights[i] + 6

    return total_w, total_h


def build_mindmap_structure(topic: str, research_data: dict | None = None) -> dict[str, Any]:
    """
    ساختار سلسله‌مراتبی مایند مپ را می‌سازد.
    اگر research_data موجود باشد از آن استفاده می‌کند،
    در غیر این صورت یک ساختار پیش‌فرض دارویی تولید می‌کند.
    """
    key_points = []
    if research_data:
        key_points = research_data.get("key_points") or []

    # اگر هنوز داده واقعی نداریم، ساختار استاندارد دارویی می‌سازیم
    if not key_points:
        key_points = [
            {
                "title": "مکانیسم اثر",
                "children": ["گیرنده هدف", "مسیر سیگنالینگ", "نتیجه بالینی"]
            },
            {
                "title": "موارد مصرف",
                "children": ["اندیکاسیون اصلی", "موارد off-label", "گروه‌های خاص"]
            },
            {
                "title": "عوارض و تداخلات",
                "children": ["عوارض شایع", "عوارض جدی", "تداخلات مهم"]
            },
            {
                "title": "نکات بالینی",
                "children": ["دوز و نحوه مصرف", "پایش بیمار", "هشدارهای مهم"]
            },
        ]

    return {
        "center": topic[:60],
        "branches": key_points
    }


def generate_mindmap_image(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
) -> str:
    """
    مایند مپ تصویری تولید می‌کند و مسیر فایل را برمی‌گرداند.
    """
    structure = build_mindmap_structure(topic, research_data)
    branches = structure["branches"]
    center_text = structure["center"]

    # اندازه تصویر
    width, height = 1600, 1200
    img = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    font_center = _load_font(28, bold=True)
    font_l1 = _load_font(20, bold=True)
    font_l2 = _load_font(16)

    cx, cy = width // 2, height // 2

    # گره مرکزی
    _draw_node(
        draw,
        (cx, cy),
        center_text,
        font_center,
        COLORS["center"],
        COLORS["center_text"],
        max_width=320,
        padding=18,
    )

    n = max(len(branches), 1)
    radius = 380  # فاصله شاخه‌های اصلی از مرکز

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n) - math.pi / 2  # شروع از بالا

        # موقعیت گره سطح ۱
        bx = int(cx + radius * math.cos(angle))
        by = int(cy + radius * math.sin(angle))

        # خط اتصال به مرکز
        draw.line([(cx, cy), (bx, by)], fill=COLORS["line"], width=4)

        title = branch.get("title", f"شاخه {i+1}") if isinstance(branch, dict) else str(branch)
        children = branch.get("children", []) if isinstance(branch, dict) else []

        _draw_node(
            draw,
            (bx, by),
            title,
            font_l1,
            COLORS["level1"],
            COLORS["level1_text"],
            max_width=200,
            padding=12,
        )

        # گره‌های سطح ۲
        if children:
            child_radius = 160
            m = len(children)
            for j, child in enumerate(children):
                # زاویه کمی بازتر حول زاویه اصلی
                spread = 0.55
                child_angle = angle - spread / 2 + (spread * j / max(m - 1, 1))
                cx2 = int(bx + child_radius * math.cos(child_angle))
                cy2 = int(by + child_radius * math.sin(child_angle))

                draw.line([(bx, by), (cx2, cy2)], fill=COLORS["line"], width=2)
                _draw_node(
                    draw,
                    (cx2, cy2),
                    str(child),
                    font_l2,
                    COLORS["level2"],
                    COLORS["level2_text"],
                    max_width=160,
                    padding=10,
                )

    # عنوان پایین تصویر
    footer_font = _load_font(14)
    footer = "Pharma Research Agent  |  مایند مپ تحقیق دارویی"
    bbox = draw.textbbox((0, 0), footer, font=footer_font)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 40), footer, font=footer_font, fill=(100, 116, 139))

    # ذخیره
    if not output_name:
        safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic[:40])
        output_name = f"mindmap_{safe_topic}.png"

    out_path = OUTPUT_DIR / output_name
    img.save(out_path, "PNG", quality=95)
    print(f"[MINDMAP] ذخیره شد → {out_path}")
    return str(out_path)


# تست سریع محلی
if __name__ == "__main__":
    path = generate_mindmap_image(
        "تداخلات دارویی متفورمین با داروهای قلبی",
        research_data={
            "key_points": [
                {"title": "مکانیسم", "children": ["کاهش گلوکونئوژنز", "حساسیت به انسولین"]},
                {"title": "تداخلات مهم", "children": ["با مهارکننده‌های ACE", "با دیورتیک‌ها", "با کنتراست"]},
                {"title": "نکات بالینی", "children": ["پایش عملکرد کلیه", "قطع قبل از تصویربرداری"]},
            ]
        },
    )
    print("تست مایند مپ انجام شد:", path)
