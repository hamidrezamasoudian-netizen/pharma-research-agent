"""
document.py – مقاله علمی PDF

مشکل قبلی: bidi روی کل جمله + شکستن خط توسط ReportLab
باعث می‌شد ابتدای جمله به انتهای سطر برود.

روش درست:
1) متن منطقی را با اندازه‌گیری عرض به سطرها بشکن
2) روی هر سطر جداگانه reshape + bidi بزن
3) هر سطر را یک Paragraph جدا بنویس
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    HAS_ARABIC = True
except Exception:
    HAS_ARABIC = False

ENABLE_DOCX = os.environ.get("ENABLE_DOCX", "false").strip().lower() in {"1", "true", "yes", "on"}

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    Path("fonts/Vazirmatn-Regular.ttf"),
    Path("fonts/Vazirmatn-Bold.ttf"),
    Path("/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]

# عرض مفید متن روی صفحه A4 با حاشیه ۲ سانتی‌متر از هر طرف
PAGE_TEXT_WIDTH = A4[0] - 4 * cm


def _find_font() -> Path | None:
    for p in FONT_CANDIDATES:
        if p.exists():
            return p
    return None


def _safe_filename(text: str, max_len: int = 50) -> str:
    text = re.sub(r"[^\w\s\-آ-یA-Za-z0-9]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:max_len] or "article"


def _xml_escape(s: str) -> str:
    return (
        str(s)
        .replace("&", "&")
        .replace("<", "<")
        .replace(">", ">")
    )


def _reshape_only(text: str) -> str:
    if not text:
        return ""
    if HAS_ARABIC:
        return arabic_reshaper.reshape(str(text))
    return str(text)


def _to_visual(text: str) -> str:
    """reshape + bidi برای یک سطر کامل (که دیگر شکسته نمی‌شود)."""
    if not text:
        return ""
    if HAS_ARABIC:
        return get_display(arabic_reshaper.reshape(str(text)))
    return str(text)


def _measure(text: str, font_name: str, font_size: float) -> float:
    """عرض تقریبی متن فارسی پس از reshape (بدون bidi)."""
    try:
        return pdfmetrics.stringWidth(_reshape_only(text), font_name, font_size)
    except Exception:
        return len(text) * font_size * 0.5


def _wrap_logical_lines(text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    """متن منطقی را کلمه‌به‌کلمه به سطرهایی که در عرض جا می‌شوند می‌شکند."""
    raw = str(text or "").strip()
    if not raw:
        return []

    lines: list[str] = []
    for block in re.split(r"\n+", raw):
        block = block.strip()
        if not block:
            continue
        words = block.split()
        if not words:
            continue
        current = words[0]
        for w in words[1:]:
            test = f"{current} {w}"
            if _measure(test, font_name, font_size) <= max_width:
                current = test
            else:
                lines.append(current)
                current = w
        lines.append(current)
    return lines


def build_article_content(topic: str, research_data: dict | None = None) -> dict[str, Any]:
    data = research_data or {}
    summary = (data.get("summary") or "").strip()
    if not summary:
        summary = f"بررسی علمی و کاربردی موضوع «{topic}» از دیدگاه داروسازی بالینی."

    key_points = data.get("key_points") or []
    sources = data.get("sources") or [
        "UpToDate / Lexicomp – Drug Monographs",
        "Iranian National Formulary و دستورالعمل‌های وزارت بهداشت",
        "مقالات peer-reviewed در PubMed / Scopus",
    ]

    findings_parts: list[str] = []
    for i, kp in enumerate(key_points, 1):
        if isinstance(kp, dict):
            title = str(kp.get("title") or f"نکته {i}")
            children = kp.get("children") or []
            findings_parts.append(f"{i}. {title}")
            for ch in children:
                findings_parts.append(f"- {ch}")
        else:
            findings_parts.append(f"{i}. {kp}")

    findings_text = "\n".join(findings_parts) if findings_parts else (
        "یافته‌های اصلی بر اساس منابع معتبر دارویی و بالینی در این بخش خلاصه می‌شوند."
    )

    return {
        "title": topic,
        "abstract": summary,
        "introduction": (
            f"موضوع «{topic}» در داروسازی بالینی اهمیت بالایی دارد. "
            f"آگاهی دقیق از مکانیسم اثر، موارد مصرف، عوارض و تداخلات برای کاهش خطاهای دارویی ضروری است."
        ),
        "methods": (
            "این بررسی بر اساس مرور منابع معتبر انجام شده است. "
            "منابع شامل مونوگراف‌های دارویی، دستورالعمل‌های ملی و مقالات علمی است."
        ),
        "findings": findings_text,
        "discussion": (
            "مدیریت صحیح دارویی نیازمند ترکیب دانش فارماکولوژی و شرایط بالینی بیمار است. "
            "توجه به گروه‌های خاص و پایش منظم می‌تواند از عوارض جدی جلوگیری کند."
        ),
        "conclusion": (
            f"موضوع «{topic}» نیازمند رویکرد مبتنی بر شواهد است. "
            f"این متن جنبه آموزشی دارد و جایگزین قضاوت بالینی متخصص نیست."
        ),
        "references": sources,
    }


def _register_pdf_font() -> str:
    font_path = _find_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("PersianFont", str(font_path)))
            print(f"[DOCUMENT] فونت PDF: {font_path}")
            return "PersianFont"
        except Exception as e:
            print(f"[DOCUMENT] ثبت فونت PDF ناموفق: {e}")
    return "Helvetica"


def create_pdf(content: dict[str, Any], output_path: Path) -> Path:
    font_name = _register_pdf_font()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # مهم: بعد از bidi، سطر دیگر نباید توسط ReportLab شکسته شود
    # بنابراین هر سطر را خودمان می‌شکنیم و Paragraph جدا می‌گذاریم
    styles.add(ParagraphStyle(
        name="TitleFa",
        fontName=font_name,
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=20,
    ))
    styles.add(ParagraphStyle(
        name="HeadingFa",
        fontName=font_name,
        fontSize=11,
        alignment=TA_RIGHT,
        spaceBefore=10,
        spaceAfter=2,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        name="BodyFa",
        fontName=font_name,
        fontSize=10,
        alignment=TA_RIGHT,
        spaceAfter=1,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        name="FooterFa",
        fontName=font_name,
        fontSize=8,
        alignment=TA_CENTER,
        textColor="#64748b",
        spaceAfter=2,
        leading=12,
    ))

    style_meta = {
        "TitleFa": (13, PAGE_TEXT_WIDTH * 0.95),
        "HeadingFa": (11, PAGE_TEXT_WIDTH),
        "BodyFa": (10, PAGE_TEXT_WIDTH),
        "FooterFa": (8, PAGE_TEXT_WIDTH * 0.95),
    }

    def add_fa_block(story_list, text: str, style_name: str):
        font_size, max_w = style_meta[style_name]
        # کمی کمتر از عرض واقعی تا حاشیه امن بماند
        safe_w = max_w * 0.98
        logical_lines = _wrap_logical_lines(text, font_name, font_size, safe_w)
        if not logical_lines:
            return
        for i, line in enumerate(logical_lines):
            visual = _to_visual(line)
            p = Paragraph(_xml_escape(visual), styles[style_name])
            story_list.append(p)

    story = []
    add_fa_block(story, content["title"], "TitleFa")
    add_fa_block(story, f"تاریخ تهیه: {datetime.now().strftime('%Y/%m/%d')}", "FooterFa")
    story.append(Spacer(1, 8))

    for heading, key in [
        ("چکیده", "abstract"),
        ("مقدمه", "introduction"),
        ("روش بررسی", "methods"),
        ("یافته‌ها", "findings"),
        ("بحث", "discussion"),
        ("نتیجه‌گیری", "conclusion"),
    ]:
        add_fa_block(story, heading, "HeadingFa")
        add_fa_block(story, content[key], "BodyFa")
        story.append(Spacer(1, 4))

    add_fa_block(story, "منابع", "HeadingFa")
    for i, ref in enumerate(content["references"], 1):
        add_fa_block(story, f"{i}. {ref}", "BodyFa")

    story.append(Spacer(1, 12))
    add_fa_block(
        story,
        "تولیدشده توسط Pharma Research Agent | صرفاً جنبه آموزشی و کمک‌تصمیم",
        "FooterFa",
    )

    doc.build(story)
    return output_path


def generate_article(
    topic: str,
    research_data: dict | None = None,
    output_basename: str | None = None,
) -> dict[str, str | None]:
    content = build_article_content(topic, research_data)

    if not output_basename:
        output_basename = f"article_{_safe_filename(topic)}"

    docx_path = None
    pdf_path = OUTPUT_DIR / f"{output_basename}.pdf"

    if not ENABLE_DOCX:
        print("[DOCUMENT] تولید Word موقتاً غیرفعال است (ENABLE_DOCX=false)")

    try:
        create_pdf(content, pdf_path)
        print(f"[DOCUMENT] PDF → {pdf_path}")
    except Exception as e:
        print(f"[DOCUMENT] خطا در PDF: {e}")
        pdf_path = None

    return {
        "docx_path": str(docx_path) if docx_path else None,
        "pdf_path": str(pdf_path) if pdf_path else None,
        "abstract": content["abstract"],
        "title": content["title"],
    }
