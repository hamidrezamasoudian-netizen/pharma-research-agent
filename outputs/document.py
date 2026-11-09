"""
document.py – تولید مقاله علمی دارویی در قالب DOCX و PDF

ساختار استاندارد مقاله‌نویسی علمی رعایت می‌شود.
این ماژول در آینده می‌تواند به Writer Agent مستقل تبدیل شود.
"""

from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from typing import Any

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_JUSTIFY

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(text: str, max_len: int = 50) -> str:
    text = re.sub(r"[^\w\s\-آ-ی]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:max_len] or "article"


def build_article_content(topic: str, research_data: dict | None = None) -> dict[str, Any]:
    """
    محتوای مقاله را بر اساس موضوع و داده‌های تحقیق می‌سازد.
    در نسخه فعلی از ساختار استاندارد + داده‌های موجود استفاده می‌کند.
    بعداً با Gemini محتوای واقعی‌تر تولید خواهد شد.
    """
    summary = (research_data or {}).get("summary") or f"بررسی علمی موضوع «{topic}» از دیدگاه داروسازی بالینی."
    key_points = (research_data or {}).get("key_points") or []
    sources = (research_data or {}).get("sources") or [
        "UpToDate / Lexicomp – Drug Monographs",
        "Iranian National Formulary & Ministry of Health guidelines",
        "PubMed / Scopus peer-reviewed articles",
    ]

    # تبدیل key_points به متن خوانا
    findings_parts = []
    for i, kp in enumerate(key_points, 1):
        if isinstance(kp, dict):
            title = kp.get("title", f"نکته {i}")
            children = kp.get("children", [])
            findings_parts.append(f"{i}. {title}")
            for ch in children:
                findings_parts.append(f"   - {ch}")
        else:
            findings_parts.append(f"{i}. {kp}")

    findings_text = "\n".join(findings_parts) if findings_parts else (
        "در این بخش یافته‌های اصلی تحقیق بر اساس منابع معتبر دارویی و بالینی ارائه می‌شود."
    )

    return {
        "title": topic,
        "abstract": (
            f"هدف: {summary}\n\n"
            "روش: مرور منابع معتبر بین‌المللی و دستورالعمل‌های ملی داروسازی.\n\n"
            "یافته‌ها: نکات کلیدی مکانیسم، موارد مصرف، عوارض و توصیه‌های بالینی استخراج شد.\n\n"
            "نتیجه‌گیری: استفاده ایمن و مبتنی بر شواهد از دارو نیازمند توجه به تداخلات، "
            "پایش بیمار و دستورالعمل‌های به‌روز است."
        ),
        "introduction": (
            f"موضوع «{topic}» از اهمیت بالایی در طبابت و داروسازی بالینی برخوردار است. "
            "با افزایش تنوع داروهای موجود و پیچیدگی رژیم‌های درمانی، آگاهی دقیق از مکانیسم اثر، "
            "اندیکاسیون‌ها، عوارض جانبی و تداخلات دارویی برای جلوگیری از خطاهای دارویی ضروری است. "
            "این مقاله با رویکرد علمی و کاربردی، مهم‌ترین جنبه‌های موضوع را بررسی می‌کند."
        ),
        "methods": (
            "این بررسی بر اساس مرور منابع معتبر انجام شده است:\n"
            "- مونوگراف‌های دارویی UpToDate و Lexicomp\n"
            "- دستورالعمل‌ها و فارماکوپه ملی ایران\n"
            "- مقالات peer-reviewed نمایه‌شده در PubMed و Scopus\n"
            "- منابع آموزشی انجمن‌های داروسازی و پزشکی\n\n"
            "اطلاعات استخراج‌شده در قالب ساختار استاندارد مقاله‌نویسی علمی سازماندهی شده‌اند."
        ),
        "findings": findings_text,
        "discussion": (
            "یافته‌های این بررسی نشان می‌دهد که مدیریت صحیح دارویی نیازمند ترکیب دانش فارماکولوژی، "
            "شرایط بالینی بیمار و توجه به تداخلات بالقوه است. "
            "توجه به گروه‌های خاص (سالمندان، بیماران کلیوی، بارداری و ...) و پایش منظم می‌تواند "
            "از بروز عوارض جدی جلوگیری کند. همچنین هماهنگی بین پزشک و داروساز نقش کلیدی در "
            "بهینه‌سازی درمان دارد."
        ),
        "conclusion": (
            f"موضوع «{topic}» نیازمند رویکرد مبتنی بر شواهد و توجه به جزئیات بالینی است. "
            "توصیه می‌شود تصمیم‌گیری درمانی همواره با در نظر گرفتن شرایط فردی بیمار، "
            "آخرین دستورالعمل‌ها و مشورت بین‌رشته‌ای انجام شود. "
            "این مقاله به‌عنوان منبع کمکی برای داروسازان و کادر درمان تهیه شده و جایگزین "
            "قضاوت بالینی متخصص نیست."
        ),
        "references": sources,
    }


def create_docx(content: dict[str, Any], output_path: Path) -> Path:
    """ساخت فایل Word با ساختار علمی و راست‌چین."""
    doc = Document()

    # تنظیمات صفحه
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.right_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    def add_heading_fa(text: str, level: int = 1):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(16 if level == 1 else 13)
        run.font.name = "Arial"
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(8)
        return p

    def add_para_fa(text: str, bold: bool = False):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.size = Pt(12)
        run.font.name = "Arial"
        run.bold = bold
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.4
        return p

    # عنوان
    title = doc.add_paragraph()
    run = title.add_run(content["title"])
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = "Arial"
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(12)

    # تاریخ
    date_p = doc.add_paragraph()
    date_run = date_p.add_run(f"تاریخ تهیه: {datetime.now().strftime('%Y/%m/%d')}")
    date_run.font.size = Pt(10)
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_heading_fa("چکیده", 1)
    add_para_fa(content["abstract"])

    add_heading_fa("مقدمه", 1)
    add_para_fa(content["introduction"])

    add_heading_fa("روش بررسی", 1)
    add_para_fa(content["methods"])

    add_heading_fa("یافته‌ها", 1)
    add_para_fa(content["findings"])

    add_heading_fa("بحث", 1)
    add_para_fa(content["discussion"])

    add_heading_fa("نتیجه‌گیری", 1)
    add_para_fa(content["conclusion"])

    add_heading_fa("منابع", 1)
    for i, ref in enumerate(content["references"], 1):
        add_para_fa(f"{i}. {ref}")

    # پاورقی
    footer = doc.add_paragraph()
    footer_run = footer.add_run("\n— تولیدشده توسط Pharma Research Agent | صرفاً جنبه آموزشی و کمک‌تصمیم —")
    footer_run.font.size = Pt(9)
    footer_run.italic = True
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(output_path)
    return output_path


def create_pdf(content: dict[str, Any], output_path: Path) -> Path:
    """ساخت PDF ساده و خوانا (راست‌چین تا حد امکان)."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # استایل‌های سفارشی (بدون وابستگی اجباری به فونت فارسی سیستم)
    styles.add(ParagraphStyle(
        name="TitleFa",
        parent=styles["Title"],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12,
        leading=22,
    ))
    styles.add(ParagraphStyle(
        name="HeadingFa",
        parent=styles["Heading2"],
        fontSize=13,
        alignment=TA_RIGHT,
        spaceBefore=14,
        spaceAfter=8,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name="BodyFa",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_RIGHT,
        spaceAfter=6,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name="FooterFa",
        parent=styles["Normal"],
        fontSize=8,
        alignment=TA_CENTER,
        textColor="#64748b",
    ))

    story = []

    story.append(Paragraph(content["title"], styles["TitleFa"]))
    story.append(Paragraph(f"تاریخ تهیه: {datetime.now().strftime('%Y/%m/%d')}", styles["FooterFa"]))
    story.append(Spacer(1, 12))

    def section(title: str, body: str):
        story.append(Paragraph(title, styles["HeadingFa"]))
        # تبدیل خط جدید به <br/>
        body_html = body.replace("\n", "<br/>")
        story.append(Paragraph(body_html, styles["BodyFa"]))

    section("چکیده", content["abstract"])
    section("مقدمه", content["introduction"])
    section("روش بررسی", content["methods"])
    section("یافته‌ها", content["findings"])
    section("بحث", content["discussion"])
    section("نتیجه‌گیری", content["conclusion"])

    story.append(Paragraph("منابع", styles["HeadingFa"]))
    for i, ref in enumerate(content["references"], 1):
        story.append(Paragraph(f"{i}. {ref}", styles["BodyFa"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "تولیدشده توسط Pharma Research Agent | صرفاً جنبه آموزشی و کمک‌تصمیم",
        styles["FooterFa"]
    ))

    doc.build(story)
    return output_path


def generate_article(
    topic: str,
    research_data: dict | None = None,
    output_basename: str | None = None,
) -> dict[str, str | None]:
    """
    مقاله کامل را در قالب DOCX و PDF تولید می‌کند و مسیر فایل‌ها را برمی‌گرداند.
    """
    content = build_article_content(topic, research_data)

    if not output_basename:
        output_basename = f"article_{_safe_filename(topic)}"

    docx_path = OUTPUT_DIR / f"{output_basename}.docx"
    pdf_path = OUTPUT_DIR / f"{output_basename}.pdf"

    create_docx(content, docx_path)
    print(f"[DOCUMENT] DOCX ذخیره شد → {docx_path}")

    try:
        create_pdf(content, pdf_path)
        print(f"[DOCUMENT] PDF ذخیره شد → {pdf_path}")
    except Exception as e:
        print(f"[DOCUMENT] خطا در ساخت PDF: {e}")
        pdf_path = None

    return {
        "docx_path": str(docx_path),
        "pdf_path": str(pdf_path) if pdf_path else None,
        "abstract": content["abstract"],
        "title": content["title"],
    }


if __name__ == "__main__":
    result = generate_article("تداخلات دارویی متفورمین با داروهای قلبی")
    print("نتیجه تست:", result)
