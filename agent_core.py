"""
agent_core.py – هسته هماهنگی Pharma Research Agent

این فایل نقش «سرپرست سبک» را بازی می‌کند.
هر بخش (تحقیق، نگارش، مایند مپ، صوت) به صورت ماژول مستقل نوشته شده
تا بعداً بتوان هر کدام را به یک ایجنت جدا تبدیل کرد.
"""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from datetime import datetime

from outputs.mindmap import generate_mindmap_image
from outputs.document import generate_article
from outputs.audio import generate_audio_summary as make_audio

STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)
HISTORY_FILE = STATE_DIR / "research_history.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(entry: dict):
    history = load_history()
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def _fallback_research(topic: str) -> dict:
    """ساختار پیش‌فرض وقتی Gemini در دسترس نیست."""
    return {
        "topic": topic,
        "summary": f"بررسی علمی و کاربردی موضوع «{topic}» از دیدگاه داروسازی بالینی.",
        "key_points": [
            {
                "title": "مکانیسم اثر",
                "children": ["گیرنده یا مسیر هدف", "اثر فارماکودینامیک", "نتیجه بالینی"]
            },
            {
                "title": "موارد مصرف",
                "children": ["اندیکاسیون اصلی", "موارد خاص", "محدودیت‌ها"]
            },
            {
                "title": "عوارض و تداخلات",
                "children": ["عوارض شایع", "عوارض جدی", "تداخلات مهم"]
            },
            {
                "title": "نکات بالینی",
                "children": ["دوز و نحوه مصرف", "پایش بیمار", "هشدارهای کلیدی"]
            },
        ],
        "sources": [
            "UpToDate / Lexicomp – Drug Monographs",
            "Iranian National Formulary & Ministry of Health guidelines",
            "PubMed / Scopus peer-reviewed articles",
        ],
    }


def _parse_gemini_json(text: str) -> dict | None:
    """استخراج JSON از پاسخ مدل."""
    text = text.strip()
    # حذف بلوک کد احتمالی
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def run_research(topic: str) -> dict:
    """
    تحقیق واقعی با Gemini.
    اگر کلید API نباشد یا خطا رخ دهد، به ساختار پیش‌فرض برمی‌گردد.
    """
    print(f"[RESEARCH] در حال تحقیق در مورد: {topic}")

    if not GEMINI_API_KEY:
        print("[RESEARCH] GEMINI_API_KEY تنظیم نشده – استفاده از ساختار پیش‌فرض")
        return _fallback_research(topic)

    prompt = f"""
تو یک داروساز بالینی و محقق علمی هستی. در مورد موضوع زیر یک خلاصه علمی دقیق، بی‌طرف و کاربردی به زبان فارسی بنویس.

موضوع: «{topic}»

فقط یک JSON معتبر برگردان (بدون متن اضافه) با این ساختار دقیق:
{{
  "summary": "۲ تا ۴ جمله خلاصه علمی و کاربردی",
  "key_points": [
    {{
      "title": "عنوان شاخه اصلی",
      "children": ["نکته فرعی ۱", "نکته فرعی ۲", "نکته فرعی ۳"]
    }}
  ],
  "sources": ["منبع ۱", "منبع ۲", "منبع ۳"]
}}

قوانین:
- حداقل ۳ و حداکثر ۵ شاخه در key_points
- هر شاخه ۲ تا ۴ child داشته باشد
- از ادعاهای قطعی درمانی و توصیه شخصی پرهیز کن
- زبان علمی، واضح و مناسب داروسازان باشد
- منابع را عمومی و معتبر بنویس (مثلاً UpToDate، PubMed، دستورالعمل وزارت بهداشت)
"""

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        raw = (response.text or "").strip()
        print(f"[RESEARCH] پاسخ Gemini دریافت شد ({len(raw)} کاراکتر)")

        parsed = _parse_gemini_json(raw)
        if not parsed:
            print("[RESEARCH] JSON معتبر نبود – استفاده از پیش‌فرض")
            return _fallback_research(topic)

        return {
            "topic": topic,
            "summary": parsed.get("summary") or _fallback_research(topic)["summary"],
            "key_points": parsed.get("key_points") or _fallback_research(topic)["key_points"],
            "sources": parsed.get("sources") or _fallback_research(topic)["sources"],
        }

    except Exception as e:
        print(f"[RESEARCH] خطا در Gemini: {e} – استفاده از پیش‌فرض")
        return _fallback_research(topic)


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
    """تولید مایند مپ تصویری"""
    print(f"[VISUALIZER] در حال ساخت مایند مپ برای: {topic}")
    try:
        path = generate_mindmap_image(topic, research_data)
        return path
    except Exception as e:
        print(f"[VISUALIZER] خطا در ساخت مایند مپ: {e}")
        return None


async def generate_audio_summary(topic: str, research_data: dict) -> str | None:
    """تولید خلاصه صوتی فارسی"""
    print(f"[AUDIO] در حال ساخت خلاصه صوتی برای: {topic}")
    try:
        path = await make_audio(topic, research_data)
        return path
    except Exception as e:
        print(f"[AUDIO] خطا: {e}")
        return None


async def handle_research_request(topic: str, update=None, context=None):
    """نقطه ورود اصلی تحقیق."""
    print(f"[CORE] شروع تحقیق برای موضوع: {topic}")

    research_data = await run_research(topic)
    document_package = await generate_document(topic, research_data)
    mindmap_file = await generate_mindmap(topic, research_data)
    audio_file = await generate_audio_summary(topic, research_data)

    save_history({
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "mindmap": mindmap_file,
        "document": document_package,
        "audio": audio_file,
    })

    if update and context:
        await send_package_to_telegram(update, document_package, mindmap_file, audio_file)

    return {
        "document": document_package,
        "mindmap": mindmap_file,
        "audio": audio_file,
        "research": research_data,
    }


async def send_package_to_telegram(update, document_package, mindmap_file, audio_file):
    """ارسال پکیج نهایی به کاربر"""
    title = document_package.get("title") or "موضوع تحقیق"

    # مایند مپ
    if mindmap_file and Path(mindmap_file).exists():
        try:
            with open(mindmap_file, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=f"مایند مپ: {title}"
                )
        except Exception as e:
            await update.message.reply_text(f"مایند مپ ساخته شد اما ارسال نشد: {e}")

    # مقاله Word
    docx_path = document_package.get("docx_path")
    if docx_path and Path(docx_path).exists():
        try:
            with open(docx_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=Path(docx_path).name,
                    caption="مقاله علمی (Word)"
                )
        except Exception as e:
            await update.message.reply_text(f"فایل Word ارسال نشد: {e}")

    # مقاله PDF
    pdf_path = document_package.get("pdf_path")
    if pdf_path and Path(pdf_path).exists():
        try:
            with open(pdf_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=Path(pdf_path).name,
                    caption="مقاله علمی (PDF)"
                )
        except Exception as e:
            await update.message.reply_text(f"فایل PDF ارسال نشد: {e}")

    # خلاصه صوتی
    if audio_file and Path(audio_file).exists():
        try:
            with open(audio_file, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    title=f"خلاصه صوتی – {title}",
                    caption="خلاصه صوتی تحقیق"
                )
        except Exception as e:
            await update.message.reply_text(f"فایل صوتی ارسال نشد: {e}")

    await update.message.reply_text(
        f"✅ پکیج تحقیق «{title}» آماده شد.\n"
        "شامل:\n"
        "• مقاله علمی (Word + PDF)\n"
        "• مایند مپ تصویری\n"
        "• خلاصه صوتی فارسی"
    )
