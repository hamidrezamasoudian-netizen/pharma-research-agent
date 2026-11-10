"""
document.py – مقاله علمی (فعلاً فقط PDF؛ Word موقتاً خاموش)
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

    def reshape_fa(text: str) -> str:
        if not text:
            return ""
        return get_display(arabic_reshaper.reshape(str(text)))
except Exception:
    def reshape_fa(text: str) -> str:
        return str(text or "")

# Word موقتاً غیرفعال
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


def _find_font() -> Path | None:
    for p in FONT_CANDIDATES:
        if p.exists():
            return p
    return None


def _safe_filename(text: str, max_len: int = 50) -> str:
    text = re.sub(r"[^\w\s\-آ-یA-Za-z0-9]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:max_len] or "article"


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
                findings_parts.append(f"   - {ch}")
        else:
            findings_parts.append(f"{i}. {kp}")

    findings_text = "\n".join(findings_parts) if findings_parts else (
        "یافته‌های اصلی بر اساس منابع معتبر دارویی و بالینی در این بخش خلاصه می‌شوند."
    )

    return {
        "title": topic,
        "abstract": (
            f"هدف: {summary}\n\n"
            "روش: مرور منابع معتبر بین‌المللی و دستورالعمل‌های ملی داروسازی.\n\n"
            "یافته‌ها: نکات کلیدی مکانیسم، موارد مصرف، عوارض، تداخلات و توصیه‌های بالینی استخراج شد.\n\n"
            "نتیجه‌گیری: استفاده ایمن و مبتنی بر شواهد نیازمند توجه به تداخلات، پایش بیمار و دستورالعمل‌های به‌روز است."
        ),
        "introduction": (
            f"موضوع «{topic}» در داروسازی بالینی اهمیت بالایی دارد. "
            "آگاهی دقیق از مکانیسم اثر، اندیکاسیون‌ها، عوارض جانبی و تداخلات دارویی برای کاهش خطاهای دارویی ضروری است. "
            "این نوشتار با رویکرد علمی و کاربردی، مهم‌ترین جنبه‌های موضوع را مرور می‌کند."
        ),
        "methods": (
            "این بررسی بر اساس مرور منابع معتبر انجام شده است:\n"
            "- مونوگراف‌های دارویی UpToDate و Lexicomp\n"
            "- دستورالعمل‌ها و فارماکوپه ملی ایران\n"
            "- مقالات peer-reviewed نمایه‌شده در PubMed و Scopus\n"
            "اطلاعات در قالب ساختار استاندارد مقاله‌نویسی علمی سازماندهی شده‌اند."
        ),
        "findings": findings_text,
        "discussion": (
            "مدیریت صحیح دارویی نیازمند ترکیب دانش فارماکولوژی، شرایط بالینی بیمار و توجه به تداخلات بالقوه است. "
            "توجه به گروه‌های خاص مانند سالمندان، بیماران کلیوی و بارداری و همچنین پایش منظم می‌تواند از عوارض جدی جلوگیری کند. "
            "هماهنگی بین پزشک و داروساز در بهینه‌سازی درمان نقش کلیدی دارد."
        ),
        "conclusion": (
            f"موضوع «{topic}» نیازمند رویکرد مبتنی بر شواهد است. "
            "تصمیم‌گیری درمانی باید با در نظر گرفتن شرایط فردی بیمار و آخرین دستورالعمل‌ها انجام شود. "
            "این متن جنبه آموزشی و کمک‌تصمیم دارد و جایگزین قضاوت بالینی متخصص نیست."
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
    styles.add(ParagraphStyle(
        name="TitleFa",
        fontName=font_name,
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=20,
    ))
    styles.add(ParagraphStyle(
        name="HeadingFa",
        fontName=font_name,
        fontSize=11,
        alignment=TA_RIGHT,
        spaceBefore=10,
        spaceAfter=4,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        name="BodyFa",
        fontName=font_name,
        fontSize=9,
        alignment=TA_RIGHT,
        spaceAfter=4,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="FooterFa",
        fontName=font_name,
        fontSize=8,
        alignment=TA_CENTER,
        textColor="#64748b",
    ))

    def fa_pdf(text: str) -> str:
        raw = str(text or "")
        lines = raw.split("\n")
        out = []
        for line in lines:
            line = (
                line.replace("&", "&")
                .replace("<", "<")
                .replace(">", ">")
            )
            out.append(reshape_fa(line))
        return "<br/>".join(out)

    story = []
    story.append(Paragraph(fa_pdf(content["title"]), styles["TitleFa"]))
    story.append(Paragraph(fa_pdf(f"تاریخ تهیه: {datetime.now().strftime('%Y/%m/%d')}"), styles["FooterFa"]))
    story.append(Spacer(1, 8))

    for heading, key in [
        ("چکیده", "abstract"),
        ("مقدمه", "introduction"),
        ("روش بررسی", "methods"),
        ("یافته‌ها", "findings"),
        ("بحث", "discussion"),
        ("نتیجه‌گیری", "conclusion"),
    ]:
        story.append(Paragraph(fa_pdf(heading), styles["HeadingFa"]))
        story.append(Paragraph(fa_pdf(content[key]), styles["BodyFa"]))

    story.append(Paragraph(fa_pdf("منابع"), styles["HeadingFa"]))
    for i, ref in enumerate(content["references"], 1):
        story.append(Paragraph(fa_pdf(f"{i}. {ref}"), styles["BodyFa"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        fa_pdf("تولیدشده توسط Pharma Research Agent | صرفاً جنبه آموزشی و کمک‌تصمیم"),
        styles["FooterFa"],
    ))

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

    if ENABLE_DOCX:
        try:
            from docx import Document  # noqa: F401
            # اگر بعداً دوباره فعال شد، می‌توان create_docx را برگرداند
            print("[DOCUMENT] DOCX فعال است اما تابع create_docx در این نسخه ساده نشده")
        except Exception as e:
            print(f"[DOCUMENT] DOCX رد شد: {e}")
    else:
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
