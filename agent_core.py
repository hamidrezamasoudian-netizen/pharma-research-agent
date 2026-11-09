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

# در آینده این importها به ایجنت‌های جدا تبدیل می‌شوند
# from research.searcher import ResearchAgent
# from research.synthesizer import WriterAgent
# from outputs.mindmap import VisualizerAgent
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

    # مرحله ۲: نگارش مقاله علمی (آینده: Writer Agent)
    document_package = await generate_document(topic, research_data)

    # مرحله ۳: مایند مپ (آینده: Visualizer Agent)
    mindmap_file = await generate_mindmap(topic, research_data)

    # مرحله ۴: خلاصه صوتی (آینده: Audio Agent)
    audio_file = await generate_audio_summary(topic, research_data)

    # ذخیره تاریخچه
    save_history({
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "status": "completed"
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
        "key_points": [],
        "sources": []
    }


async def generate_document(topic: str, research_data: dict) -> dict:
    """جایگزین Writer Agent – فعلاً اسکلت"""
    print(f"[WRITER] در حال تولید مقاله برای: {topic}")
    # TODO: ساخت DOCX و PDF با ساختار علمی
    return {
        "docx_path": None,
        "pdf_path": None,
        "abstract": research_data.get("summary", "")
    }


async def generate_mindmap(topic: str, research_data: dict) -> str | None:
    """جایگزین Visualizer Agent – فعلاً اسکلت"""
    print(f"[VISUALIZER] در حال ساخت مایند مپ برای: {topic}")
    # TODO: تولید تصویر مایند مپ
    return None


async def generate_audio_summary(topic: str, research_data: dict) -> str | None:
    """جایگزین Audio Agent – فعلاً اسکلت"""
    print(f"[AUDIO] در حال ساخت خلاصه صوتی برای: {topic}")
    # TODO: تولید فایل صوتی با edge-tts
    return None


async def send_package_to_telegram(update, document_package, mindmap_file, audio_file):
    """ارسال پکیج نهایی به کاربر"""
    await update.message.reply_text(
        "تحقیق تکمیل شد.\n"
        "(در نسخه‌های بعدی فایل‌های DOCX، PDF، مایند مپ و صوت اینجا ارسال می‌شوند)"
    )
