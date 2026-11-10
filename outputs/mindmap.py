"""
mindmap.py – مایند مپ لاتین با جزئیات واقعی (نه فقط کلمات کلی)
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

# فقط عبارات نسبتاً مشخص (کوتاه‌های مبهم مثل «مصرف» اینجا نیستند)
FA_TO_EN = {
    "مکانیسم و فارماکولوژی": "Mechanism & pharmacology",
    "مکانیسم اثر": "Mechanism of action",
    "مکانیسم": "Mechanism",
    "فارماکولوژی": "Pharmacology",
    "موارد مصرف": "Indications",
    "اندیکاسیون اصلی": "Primary indication",
    "اندیکاسیون": "Indication",
    "عوارض شایع و جدی": "Common & serious AEs",
    "عوارض شایع": "Common adverse effects",
    "عوارض جدی": "Serious adverse effects",
    "عوارض جانبی": "Adverse effects",
    "عوارض": "Adverse effects",
    "تداخلات مهم": "Important interactions",
    "تداخلات دارویی": "Drug interactions",
    "تداخلات غذایی": "Food interactions",
    "تداخلات": "Interactions",
    "نکات بالینی و پایش": "Clinical monitoring",
    "پایش بیمار": "Patient monitoring",
    "پایش": "Monitoring",
    "کنتراست و تصویربرداری": "Contrast imaging",
    "مسیر اثر اصلی": "Main pathway",
    "مسیر اثر": "Pathway",
    "شروع و مدت اثر": "Onset/duration",
    "شروع اثر": "Onset",
    "متابولیسم و دفع": "Metabolism/excretion",
    "متابولیسم": "Metabolism",
    "محدودیت‌های مصرف": "Use limitations",
    "محدودیت‌ها": "Limitations",
    "گروه خاص": "Special populations",
    "موارد خاص": "Special cases",
    "علائم نیازمند مراجعه": "When to seek care",
    "علائم هشدار": "Warning signs",
    "نکته احتیاطی": "Precaution",
    "دوز و نحوه مصرف": "Dosing",
    "آموزش بیمار": "Patient counseling",
    "کاهش فشار خون": "Hypotension",
    "فشار خون وضعیتی": "Orthostatic hypotension",
    "سرگیجه": "Dizziness",
    "خستگی": "Fatigue",
    "اختلال انزال": "Ejaculation disorder",
    "انزال پس‌رو": "Retrograde ejaculation",
    "احتقان بینی": "Nasal congestion",
    "سردرد": "Headache",
    "تامسولوسین": "Tamsulosin",
    "آلفا بلوکر": "Alpha blocker",
    "پروستات": "Prostate",
    "BPH": "BPH",
    "هایپرپلازی پروستات": "BPH",
}

WORD_MAP = {
    "سرگیجه": "dizziness",
    "سردرد": "headache",
    "خستگی": "fatigue",
    "تهوع": "nausea",
    "اسهال": "diarrhea",
    "یبوست": "constipation",
    "خارش": "itching",
    "راش": "rash",
    "کهیر": "urticaria",
    "تنگی نفس": "dyspnea",
    "تپش": "palpitation",
    "افزایش": "increase",
    "کاهش": "decrease",
    "فشار": "pressure",
    "خون": "blood",
    "کلیه": "kidney",
    "کبد": "liver",
    "قلب": "heart",
    "ادرار": "urine",
    "مثانه": "bladder",
    "پروستات": "prostate",
    "انزال": "ejaculation",
    "اختلال": "disorder",
    "شایع": "common",
    "جدی": "serious",
    "نادر": "rare",
    "هشدار": "warning",
    "دوز": "dose",
    "قرص": "tablet",
    "کپسول": "capsule",
    "روزانه": "daily",
    "شب": "night",
    "صبح": "morning",
}


def _extract_latin(text: str) -> str:
    parts = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text or "")
    return " ".join(parts).strip()


def to_latin_label(text: str, max_len: int = 42) -> str:
    t = str(text or "").strip()
    if not t:
        return "Item"

    # اگر تقریباً لاتین است
    if re.search(r"[A-Za-z]", t) and not re.search(r"[\u0600-\u06FF]", t):
        return t[:max_len]

    latin = _extract_latin(t)

    # تطبیق دقیق
    if t in FA_TO_EN:
        label = FA_TO_EN[t]
        if latin and latin.lower() not in label.lower():
            label = f"{latin}: {label}"
        return label[:max_len]

    # طولانی‌ترین عبارت (≥۴ کاراکتر) — نه کلمه‌های خیلی کوتاه
    best = None
    for fa, en in sorted(FA_TO_EN.items(), key=lambda x: len(x[0]), reverse=True):
        if len(fa) >= 4 and fa in t:
            best = en
            break

    # ترجمه کلمه‌ای برای حفظ جزئیات
    words = []
    for fa, en in sorted(WORD_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if fa in t and en not in words:
            words.append(en)
        if len(words) >= 5:
            break

    pieces = []
    if latin:
        pieces.append(latin)
    if best:
        pieces.append(best)
    if words:
        pieces.append("/".join(words[:4]))

    if pieces:
        # حذف تکراری
        seen = set()
        uniq = []
        for p in pieces:
            key = p.lower()
            if key not in seen:
                seen.add(key)
                uniq.append(p)
        return " | ".join(uniq)[:max_len]

    if latin:
        return latin[:max_len]

    # آخرین راه: برچسب یکتا ولی قابل‌ردیابی
    return f"Detail-{abs(hash(t)) % 10000}"[:max_len]


def _load_font(size: int, bold: bool = False):
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
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


def _draw_node(draw, center, text, font, fill, text_color, max_width=240, padding=10):
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
    total_w = max(max_line_w + 2 * padding, 80)
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
            {"title": "Mechanism", "children": ["Alpha-1A blockade", "Smooth muscle relaxation", "Urinary flow"]},
            {"title": "Adverse effects", "children": ["Orthostatic hypotension", "Dizziness", "Ejaculation disorder"]},
            {"title": "Interactions", "children": ["Other alpha blockers", "PDE5 inhibitors", "CYP3A4 inhibitors"]},
            {"title": "Monitoring", "children": ["BP check", "Symptom response", "Counseling"]},
        ]

    normalized = []
    for kp in key_points[:5]:
        if isinstance(kp, dict):
            title = to_latin_label(kp.get("title") or "Branch", 36)
            children = [to_latin_label(c, 40) for c in (kp.get("children") or []) if str(c).strip()][:4]
            if not children:
                children = ["See full report"]
            normalized.append({"title": title, "children": children})
        else:
            normalized.append({"title": to_latin_label(kp, 36), "children": ["See full report"]})

    center = to_latin_label(topic, 44)
    return {"center": center, "branches": normalized}


def generate_mindmap_image(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
) -> str:
    structure = build_mindmap_structure(topic, research_data)
    branches = structure["branches"]
    center_text = structure["center"]

    width, height = 1800, 1350
    img = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    font_center = _load_font(17, bold=True)
    font_l1 = _load_font(13, bold=True)
    font_l2 = _load_font(11, bold=False)
    font_footer = _load_font(11)

    cx, cy = width // 2, height // 2
    _draw_node(draw, (cx, cy), center_text, font_center, COLORS["center"], COLORS["center_text"], 360, 12)

    n = max(len(branches), 1)
    radius = 400

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n) - math.pi / 2
        bx = int(cx + radius * math.cos(angle))
        by = int(cy + radius * math.sin(angle))
        draw.line([(cx, cy), (bx, by)], fill=COLORS["line"], width=3)

        title = branch.get("title", f"Branch {i+1}")
        children = branch.get("children") or []
        _draw_node(draw, (bx, by), title, font_l1, COLORS["level1"], COLORS["level1_text"], 220, 8)

        if children:
            m = len(children)
            child_radius = 170
            spread = min(0.95, 0.34 + 0.14 * m)
            for j, child in enumerate(children):
                child_angle = angle if m == 1 else angle - spread / 2 + (spread * j / (m - 1))
                cx2 = int(bx + child_radius * math.cos(child_angle))
                cy2 = int(by + child_radius * math.sin(child_angle))
                cx2 = max(90, min(width - 90, cx2))
                cy2 = max(55, min(height - 70, cy2))
                draw.line([(bx, by), (cx2, cy2)], fill=COLORS["line"], width=2)
                _draw_node(draw, (cx2, cy2), str(child), font_l2, COLORS["level2"], COLORS["level2_text"], 200, 6)

    footer = "Pharma Research Agent | detailed Latin mindmap"
    bbox = draw.textbbox((0, 0), footer, font=font_footer)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 32), footer, font=font_footer, fill=(100, 116, 139))

    if not output_name:
        safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", to_latin_label(topic, 40))
        output_name = f"mindmap_{safe}.png"

    out_path = OUTPUT_DIR / output_name
    img.save(out_path, "PNG")
    print(f"[MINDMAP] detailed Latin → {out_path}")
    return str(out_path)
