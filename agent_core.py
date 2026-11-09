"""
agent_core.py – هسته هماهنگی Pharma Research Agent

این فایل نقش «سرپرست سبک» را بازی می‌کند.
هر بخش (تحقیق، نگارش، مایند مپ، صوت) به صورت ماژول مستقل نوشته شده
تا بعداً بتوان هر کدام را به یک ایجنت جدا تبدیل کرد.
"""

import os
import json
from pathlib import Path
from datetime import datetime

from outputs.mindmap import generate_mindmap_image
from outputs.document import generate_article

# در آینده این importها به ایجنت‌های جدا تبدیل می‌شوند
# from research.searcher import ResearchAgent
# from outputs.audio import AudioAgent

STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)
HISTORY_FILE = STATE_DIR / "research_history.json"


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(entry: dict):
    history = load_history()
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


async def handle_research_request(topic: str, update=None, context=None):
    """
    نقطه ورود اصلی تحقیق.
    در نسخه فعلی همه کارها اینجا هماهنگ می‌شود.
    در نسخه مولتی‌ایجنت، این تابع فقط موضوع را به Supervisor می‌دهد.
    """
    print(f"[CORE] شروع تحقیق برای موضوع: {topic}")

    # مرحله ۱: تحقیق و جمع‌آوری منابع (آینده: Research Agent)
    research_data = await run_research(topic)

    # مرحله ۲: نگارش مقاله علمی (Writer)
    document_package = await generate_document(topic, research_data)

    # مرحله ۳: مایند مپ (Visualizer)
    mindmap_file = await generate_mindmap(topic, research_data)

    # مرحله ۴: خلاصه صوتی (آینده: Audio Agent)
    audio_file = await generate_audio_summary(topic, research_data)

    # ذخیره تاریخچه
    save_history({
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "mindmap": mindmap_file,
        "document": document_package,
    })

    # ارسال به تلگرام (اگر در دسترس باشد)
    if update and context:
        await send_package_to_telegram(update, document_package, mindmap_file, audio_file)

    return {
        "document": document_package,
        "mindmap": mindmap_file,
        "audio": audio_file
    }


async def run_research(topic: str) -> dict:
    """جایگزین Research Agent – فعلاً اسکلت"""
    print(f"[RESEARCH] در حال تحقیق در مورد: {topic}")
    # TODO: اتصال به Gemini + جستجوی منابع
    return {
        "topic": topic,
        "summary": f"خلاصه اولیه تحقیق در مورد {topic}",
        "key_points": [
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
        ],
        "sources": [
            "UpToDate / Lexicomp – Drug Monographs",
            "Iranian National Formulary & Ministry of Health guidelines",
            "PubMed / Scopus peer-reviewed articles",
        ]
    }


async def generate_document(topic: str, research_data: dict) -> dict:
    """تولید مقاله علمی DOCX + PDF"""
    print(f"[WRITER] در حال تولید مقاله برای: {topic}")
    try:
        result = generate_article(topic, research_data)
        return result
    except Exception as e:
        print(f"[WRITER] خطا در تولید مقاله: {e}")
        return {
            "docx_path": None,
            "pdf_path": None,
            "abstract": research_data.get("summary", ""),
            "title": topic,
        }


async def generate_mindmap(topic: str, research_data: dict) -> str | None:
    """تولید مایند مپ تصویری با ماژول outputs.mindmap"""
    print(f"[VISUALIZER] در حال ساخت مایند مپ برای: {topic}")
    try:
        path = generate_mindmap_image(topic, research_data)
        return path
    except Exception as e:
        print(f"[VISUALIZER] خطا در ساخت مایند مپ: {e}")
        return None


async def generate_audio_summary(topic: str, research_data: dict) -> str | None:
    """جایگزین Audio Agent – فعلاً اسکلت"""
    print(f"[AUDIO] در حال ساخت خلاصه صوتی برای: {topic}")
    # TODO: تولید فایل صوتی با edge-tts
    return None


async def send_package_to_telegram(update, document_package, mindmap_file, audio_file):
    """ارسال پکیج نهایی به کاربر"""
    title = document_package.get("title") or "موضوع تحقیق"

    # ارسال مایند مپ
    if mindmap_file and Path(mindmap_file).exists():
        try:
            with open(mindmap_file, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=f"مایند مپ: {title}"
                )
        except Exception as e:
            await update.message.reply_text(f"مایند مپ ساخته شد اما ارسال نشد: {e}")

    # ارسال فایل‌های مقاله
    docx_path = document_package.get("docx_path")
    pdf_path = document_package.get("pdf_path")

    if docx_path and Path(docx_path).exists():
        try:
            with open(docx_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=Path(docx_path).name,
                    caption="مقاله علمی (Word)"
                )
        except Exception as e:
            await update.message.reply_text(f"فایل Word ساخته شد اما ارسال نشد: {e}")

    if pdf_path and Path(pdf_path).exists():
        try:
            with open(pdf_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=Path(pdf_path).name,
                    caption="مقاله علمی (PDF)"
                )
        except Exception as e:
            await update.message.reply_text(f"فایل PDF ساخته شد اما ارسال نشد: {e}")

    await update.message.reply_text(
        f"پکیج تحقیق «{title}» آماده شد.\n"
        "شامل: مقاله علمی (Word + PDF) و مایند مپ تصویری."
    )
