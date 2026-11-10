"""
document.py – تولید مقاله علمی دارویی (DOCX + PDF) با پشتیبانی صحیح فارسی
"""

from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from typing import Any

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# مسیرهای احتمالی فونت فارسی
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


def _set_run_font(run, name: str = "Tahoma", size: int = 12, bold: bool = False):
    """فونت فارسی برای بخش Complex Script در Word"""
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = name
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:cs"), name)  # Complex Script = فارسی/عربی
    rFonts.set(qn("w:eastAsia"), name)


def _set_paragraph_rtl(paragraph):
    """راست‌چین واقعی پاراگراف"""
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    pPr.append(bidi)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT


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
                findings_parts.append(f"   • {ch}")
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
            "• مونوگراف‌های دارویی UpToDate و Lexicomp\n"
            "• دستورالعمل‌ها و فارماکوپه ملی ایران\n"
            "• مقالات peer-reviewed نمایه‌شده در PubMed و Scopus\n"
            "اطلاعات در قالب ساختار استاندارد مقاله‌نویسی علمی سازماندهی شده‌اند."
        ),
        "findings": findings_text,
        "discussion": (
            "مدیریت صحیح دارویی نیازمند ترکیب دانش فارماکولوژی، شرایط بالینی بیمار و توجه به تداخلات بالقوه است. "
            "توجه به گروه‌های خاص (سالمندان، بیماران کلیوی، بارداری و ...) و پایش منظم می‌تواند از عوارض جدی جلوگیری کند. "
            "هماهنگی بین پزشک و داروساز در بهینه‌سازی درمان نقش کلیدی دارد."
        ),
        "conclusion": (
            f"موضوع «{topic}» نیازمند رویکرد مبتنی بر شواهد است. "
            "تصمیم‌گیری درمانی باید با در نظر گرفتن شرایط فردی بیمار و آخرین دستورالعمل‌ها انجام شود. "
            "این متن جنبه آموزشی و کمک‌تصمیم دارد و جایگزین قضاوت بالینی متخصص نیست."
        ),
        "references": sources,
    }


def create_docx(content: dict[str, Any], output_path: Path) -> Path:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.right_margin = Cm(2.2)
    section.left_margin = Cm(2.2)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)

    font_name = "Tahoma"  # در ویندوز/آفیس فارسی معمولاً موجود است

    def add_heading_fa(text: str):
        p = doc.add_paragraph()
        run = p.add_run(text)
        _set_run_font(run, font_name, 14, bold=True)
        _set_paragraph_rtl(p)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        return p

    def add_para_fa(text: str, size: int = 12, bold: bool = False, center: bool = False):
        # پاراگراف‌های چندخطی را جدا می‌کنیم تا RTL بهتر اعمال شود
        for line in str(text).split("\n"):
            line = line.strip()
            if not line:
                continue
            p = doc.add_paragraph()
            run = p.add_run(line)
            _set_run_font(run, font_name, size, bold=bold)
            if center:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                _set_paragraph_rtl(p)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.35

    # عنوان
    title_p = doc.add_paragraph()
    title_run = title_p.add_run(content["title"])
    _set_run_font(title_run, font_name, 16, bold=True)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(8)

    date_p = doc.add_paragraph()
    date_run = date_p.add_run(f"تاریخ تهیه: {datetime.now().strftime('%Y/%m/%d')}")
    _set_run_font(date_run, font_name, 10)
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for heading, key in [
        ("چکیده", "abstract"),
        ("مقدمه", "introduction"),
        ("روش بررسی", "methods"),
        ("یافته‌ها", "findings"),
        ("بحث", "discussion"),
        ("نتیجه‌گیری", "conclusion"),
    ]:
        add_heading_fa(heading)
        add_para_fa(content[key])

    add_heading_fa("منابع")
    for i, ref in enumerate(content["references"], 1):
        add_para_fa(f"{i}. {ref}")

    footer = doc.add_paragraph()
    fr = footer.add_run("تولیدشده توسط Pharma Research Agent | صرفاً جنبه آموزشی و کمک‌تصمیم")
    _set_run_font(fr, font_name, 9)
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(output_path)
    return output_path


def _register_pdf_font() -> str:
    """ثبت فونت فارسی برای ReportLab؛ در صورت نبود، Helvetica (ممکن است فارسی نکند)"""
    font_path = _find_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("PersianFont", str(font_path)))
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
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=22,
        wordWrap="RTL",
    ))
    styles.add(ParagraphStyle(
        name="HeadingFa",
        fontName=font_name,
        fontSize=12,
        alignment=TA_RIGHT,
        spaceBefore=12,
        spaceAfter=6,
        leading=18,
        wordWrap="RTL",
    ))
    styles.add(ParagraphStyle(
        name="BodyFa",
        fontName=font_name,
        fontSize=10,
        alignment=TA_RIGHT,
        spaceAfter=5,
        leading=16,
        wordWrap="RTL",
    ))
    styles.add(ParagraphStyle(
        name="FooterFa",
        fontName=font_name,
        fontSize=8,
        alignment=TA_CENTER,
        textColor="#64748b",
    ))

    def fa(text: str) -> str:
        # کاراکترهای خاص XML
        return (
            str(text)
            .replace("&", "&")
            .replace("<", "<")
            .replace(">", ">")
            .replace("\n", "<br/>")
        )

    story = []
    story.append(Paragraph(fa(content["title"]), styles["TitleFa"]))
    story.append(Paragraph(fa(f"تاریخ تهیه: {datetime.now().strftime('%Y/%m/%d')}"), styles["FooterFa"]))
    story.append(Spacer(1, 10))

    for heading, key in [
        ("چکیده", "abstract"),
        ("مقدمه", "introduction"),
        ("روش بررسی", "methods"),
        ("یافته‌ها", "findings"),
        ("بحث", "discussion"),
        ("نتیجه‌گیری", "conclusion"),
    ]:
        story.append(Paragraph(fa(heading), styles["HeadingFa"]))
        story.append(Paragraph(fa(content[key]), styles["BodyFa"]))

    story.append(Paragraph(fa("منابع"), styles["HeadingFa"]))
    for i, ref in enumerate(content["references"], 1):
        story.append(Paragraph(fa(f"{i}. {ref}"), styles["BodyFa"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        fa("تولیدشده توسط Pharma Research Agent | صرفاً جنبه آموزشی و کمک‌تصمیم"),
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

    docx_path = OUTPUT_DIR / f"{output_basename}.docx"
    pdf_path = OUTPUT_DIR / f"{output_basename}.pdf"

    create_docx(content, docx_path)
    print(f"[DOCUMENT] DOCX → {docx_path}")

    try:
        create_pdf(content, pdf_path)
        print(f"[DOCUMENT] PDF → {pdf_path}")
    except Exception as e:
        print(f"[DOCUMENT] خطا در PDF: {e}")
        pdf_path = None

    return {
        "docx_path": str(docx_path),
        "pdf_path": str(pdf_path) if pdf_path else None,
        "abstract": content["abstract"],
        "title": content["title"],
    }
