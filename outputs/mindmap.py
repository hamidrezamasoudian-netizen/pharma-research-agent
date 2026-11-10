"""
mindmap.py – مایند مپ با برچسب‌های لاتین (موقت) برای جلوگیری از برعکس‌نویسی فارسی
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

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

# نگاشت تقریبی فارسی → لاتین برای نمایش موقت
FA_TO_EN = {
    "مکانیسم": "Mechanism",
    "مکانیسم اثر": "Mechanism",
    "مکانیسم و فارماکولوژی": "Pharmacology",
    "فارماکولوژی": "Pharmacology",
    "موارد مصرف": "Indications",
    "مصرف": "Use",
    "عوارض": "Adverse effects",
    "عوارض شایع و جدی": "Adverse effects",
    "تداخلات": "Interactions",
    "تداخلات مهم": "Interactions",
    "تداخل با داروهای قلبی": "Cardiac drug interactions",
    "پایش": "Monitoring",
    "نکات بالینی و پایش": "Clinical monitoring",
    "کنتراست و تصویربرداری": "Contrast imaging",
    "مسیر اثر": "Pathway",
    "مسیر اثر اصلی": "Main pathway",
    "شروع اثر": "Onset",
    "شروع و مدت اثر": "Onset/duration",
    "متابولیسم": "Metabolism",
    "متابولیسم و دفع": "Metabolism/excretion",
    "اندیکاسیون": "Indication",
    "اندیکاسیون اصلی": "Primary indication",
    "محدودیت": "Limitation",
    "محدودیت‌ها": "Limitations",
    "محدودیت‌های مصرف": "Use limits",
    "گروه خاص": "Special groups",
    "موارد خاص": "Special cases",
    "شایع": "Common",
    "عوارض شایع": "Common AEs",
    "جدی": "Serious",
    "عوارض جدی": "Serious AEs",
    "هشدار": "Warning",
    "علائم هشدار": "Warning signs",
    "علائم نیازمند مراجعه": "Seek care signs",
    "دارویی": "Drug-drug",
    "تداخلات دارویی": "Drug-drug",
    "غذایی": "Food",
    "تداخلات غذایی": "Food interactions",
    "احتیاط": "Caution",
    "نکته احتیاطی": "Caution",
    "دوز": "Dose",
    "دوز و نحوه مصرف": "Dosing",
    "آزمایش": "Labs",
    "آموزش": "Counseling",
    "آموزش بیمار": "Patient counseling",
    "پایش بیمار": "Patient monitoring",
    "کاهش گلوکونئوژنز کبدی": "Less hepatic gluconeogenesis",
    "افزایش حساسیت به انسولین": "Insulin sensitivity",
    "کاهش جذب روده‌ای گلوکز": "Less GI glucose uptake",
    "مهارکننده ACE و ARB و خطر افت عملکرد کلیه": "ACE/ARB kidney risk",
    "دیورتیک‌ها و کم‌آبی": "Diuretics/dehydration",
    "داروهای مؤثر بر پرفیوژن کلیوی": "Renal perfusion drugs",
    "اسیدوز لاکتیک نادر اما خطرناک": "Lactic acidosis risk",
    "اختلال گوارشی شایع در شروع": "GI upset early",
    "کمبود ویتامین B12 در مصرف طولانی": "B12 deficiency long-term",
    "قطع موقت قبل از کنتراست یددار": "Hold before iodinated contrast",
    "ارزیابی eGFR": "Check eGFR",
    "شروع مجدد پس از اطمینان از عملکرد کلیه": "Restart after renal OK",
    "کراتینین و eGFR منظم": "Creatinine/eGFR",
    "علائم اسیدوز و کم‌آبی": "Acidosis/dehydration signs",
    "آموزش بیمار درباره قطع در بیماری حاد": "Sick-day rules",
}


def to_latin_label(text: str, max_len: int = 34) -> str:
    t = str(text or "").strip()
    if not t:
        return "Item"
    if t in FA_TO_EN:
        return FA_TO_EN[t][:max_len]
    # اگر از قبل لاتین بود
    if re.search(r"[A-Za-z]", t) and not re.search(r"[\u0600-\u06FF]", t):
        return t[:max_len]
    # نگاشت جزئی
    for fa, en in FA_TO_EN.items():
        if fa in t:
            return en[:max_len]
    # اگر فارسی بود و ترجمه نداشت: کد کوتاه لاتین
    ascii_only = re.sub(r"[^A-Za-z0-9\s\-/]", "", t).strip()
    if ascii_only:
        return ascii_only[:max_len]
    return ("Topic " + str(abs(hash(t)) % 1000))[:max_len]


def _load_font(size: int, bold: bool = False):
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("fonts/Vazirmatn-Regular.ttf"),
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
        bbox = draw.textbbox((0, 0), test, font=font)
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
    lines = _wrap_text(text, font, max_width - 2 * padding, draw)
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
            {"title": "Mechanism", "children": ["Pathway", "Onset", "Metabolism"]},
            {"title": "Indications", "children": ["Primary use", "Limits", "Special groups"]},
            {"title": "Adverse effects", "children": ["Common", "Serious", "Warnings"]},
            {"title": "Interactions", "children": ["Drug-drug", "Food", "Caution"]},
            {"title": "Monitoring", "children": ["Dose", "Labs", "Counseling"]},
        ]

    normalized = []
    for kp in key_points[:5]:
        if isinstance(kp, dict):
            title = to_latin_label(kp.get("title") or "Branch", 28)
            children = [to_latin_label(c, 26) for c in (kp.get("children") or []) if str(c).strip()][:3]
            if not children:
                children = ["Details"]
            normalized.append({"title": title, "children": children})
        else:
            normalized.append({"title": to_latin_label(kp, 28), "children": ["Details"]})

    center = to_latin_label(topic, 40)
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

    font_center = _load_font(18, bold=True)
    font_l1 = _load_font(14, bold=True)
    font_l2 = _load_font(12, bold=False)
    font_footer = _load_font(11)

    cx, cy = width // 2, height // 2
    _draw_node(draw, (cx, cy), center_text, font_center, COLORS["center"], COLORS["center_text"], 320, 12)

    n = max(len(branches), 1)
    radius = 380

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n) - math.pi / 2
        bx = int(cx + radius * math.cos(angle))
        by = int(cy + radius * math.sin(angle))
        draw.line([(cx, cy), (bx, by)], fill=COLORS["line"], width=3)

        title = branch.get("title", f"Branch {i+1}")
        children = branch.get("children") or []
        _draw_node(draw, (bx, by), title, font_l1, COLORS["level1"], COLORS["level1_text"], 200, 8)

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
                _draw_node(draw, (cx2, cy2), str(child), font_l2, COLORS["level2"], COLORS["level2_text"], 170, 6)

    footer = "Pharma Research Agent | Latin labels (temporary)"
    bbox = draw.textbbox((0, 0), footer, font=font_footer)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 32), footer, font=font_footer, fill=(100, 116, 139))

    if not output_name:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in to_latin_label(topic, 40))
        output_name = f"mindmap_{safe}.png"

    out_path = OUTPUT_DIR / output_name
    img.save(out_path, "PNG")
    print(f"[MINDMAP] Latin labels → {out_path}")
    return str(out_path)
