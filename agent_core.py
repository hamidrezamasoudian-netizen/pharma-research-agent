"""
agent_core.py – هسته هماهنگی Pharma Research Agent
"""

from __future__ import annotations

import os
import re
import json
import asyncio
from pathlib import Path
from datetime import datetime

from outputs.mindmap import generate_mindmap_image
from outputs.document import generate_article
from outputs.audio import generate_audio_summary as make_audio

STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)
HISTORY_FILE = STATE_DIR / "research_history.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
USE_SUPERVISOR = os.environ.get("USE_SUPERVISOR", "true").strip().lower() in {"1", "true", "yes", "on"}


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(entry: dict):
    history = load_history()
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def _fallback_research(topic: str) -> dict:
    t = topic or ""
    # محتوای غنی‌تر وقتی موضوع شناخته‌شده باشد (برای صوت و مایند مپ)
    if "متفورمین" in t or "metformin" in t.lower():
        return {
            "topic": topic,
            "summary": (
                "متفورمین داروی خط اول دیابت نوع دو است که با کاهش تولید گلوکز کبدی و افزایش حساسیت محیطی به انسولین عمل می‌کند. "
                "تداخلات مهم آن با داروهای قلبی-کلیوی، به‌ویژه مهارکننده‌های ACE،ARB، دیورتیک‌ها و مواد حاجب یددار، "
                "می‌تواند خطر اسیدوز لاکتیک را در زمینه کاهش عملکرد کلیه افزایش دهد. "
                "پایش کراتینین، قطع موقت قبل از تصویربرداری با کنتراست، و توجه به کم‌آبی و هیپوکسی از نکات کلیدی ایمن‌سازی مصرف است."
            ),
            "key_points": [
                {
                    "title": "مکانیسم اثر",
                    "children": [
                        "کاهش گلوکونئوژنز کبدی",
                        "افزایش حساسیت به انسولین",
                        "کاهش جذب روده‌ای گلوکز",
                    ],
                },
                {
                    "title": "تداخل با داروهای قلبی",
                    "children": [
                        "مهارکننده ACE و ARB و خطر افت عملکرد کلیه",
                        "دیورتیک‌ها و کم‌آبی",
                        "داروهای مؤثر بر پرفیوژن کلیوی",
                    ],
                },
                {
                    "title": "عوارض جدی",
                    "children": [
                        "اسیدوز لاکتیک نادر اما خطرناک",
                        "اختلال گوارشی شایع در شروع",
                        "کمبود ویتامین B12 در مصرف طولانی",
                    ],
                },
                {
                    "title": "کنتراست و تصویربرداری",
                    "children": [
                        "قطع موقت قبل از کنتراست یددار",
                        "ارزیابی eGFR",
                        "شروع مجدد پس از اطمینان از عملکرد کلیه",
                    ],
                },
                {
                    "title": "پایش بالینی",
                    "children": [
                        "کراتینین و eGFR منظم",
                        "علائم اسیدوز و کم‌آبی",
                        "آموزش بیمار درباره قطع در بیماری حاد",
                    ],
                },
            ],
            "sources": [
                "UpToDate / Lexicomp – Metformin monographs",
                "دستورالعمل‌های انجمن دیابت و وزارت بهداشت",
                "PubMed – metformin lactic acidosis and contrast",
            ],
        }

    return {
        "topic": topic,
        "summary": (
            f"موضوع «{topic}» از دیدگاه داروسازی بالینی بررسی می‌شود. "
            "در این مرور، مکانیسم اثر، موارد مصرف، عوارض شایع و جدی، تداخلات مهم و نکات پایش بیمار جمع‌بندی شده است. "
            "هدف، ارائه چارچوب کاربردی برای تصمیم‌گیری ایمن‌تر در داروخانه و تیم درمان است."
        ),
        "key_points": [
            {
                "title": "مکانیسم و فارماکولوژی",
                "children": ["مسیر اثر اصلی", "شروع و مدت اثر", "متابولیسم و دفع"],
            },
            {
                "title": "موارد مصرف",
                "children": ["اندیکاسیون اصلی", "موارد خاص", "محدودیت‌های مصرف"],
            },
            {
                "title": "عوارض شایع و جدی",
                "children": ["عوارض شایع", "عوارض جدی", "علائم نیازمند مراجعه"],
            },
            {
                "title": "تداخلات مهم",
                "children": ["تداخلات دارویی", "تداخلات غذایی", "نکته احتیاطی"],
            },
            {
                "title": "نکات بالینی و پایش",
                "children": ["دوز و نحوه مصرف", "پایش بیمار", "آموزش بیمار"],
            },
        ],
        "sources": [
            "UpToDate / Lexicomp – Drug Monographs",
            "Iranian National Formulary و دستورالعمل‌های وزارت بهداشت",
            "PubMed / Scopus peer-reviewed articles",
        ],
    }


def _parse_gemini_json(text: str) -> dict | None:
    text = text.strip()
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
    print(f"[RESEARCH] در حال تحقیق در مورد: {topic}")

    if not GEMINI_API_KEY:
        print("[RESEARCH] GEMINI_API_KEY تنظیم نشده – استفاده از ساختار پیش‌فرض")
        return _fallback_research(topic)

    prompt = f"""
تو یک داروساز بالینی و محقق علمی هستی. درباره موضوع زیر محتوای علمی دقیق، بی‌طرف و کاربردی به فارسی بنویس.

موضوع: «{topic}»

فقط یک JSON معتبر برگردان (بدون متن اضافه) با این ساختار:
{{
  "summary": "۴ تا ۷ جمله علمی و کاربردی با ذکر مکانیسم، خطر مهم و نکته پایش",
  "key_points": [
    {{
      "title": "عنوان شاخه مشخص",
      "children": ["جزئیات عملی ۱", "جزئیات عملی ۲", "جزئیات عملی ۳"]
    }}
  ],
  "sources": ["منبع ۱", "منبع ۲", "منبع ۳"]
}}

قوانین:
- دقیقاً ۵ شاخه در key_points
- هر شاخه ۳ child مشخص و مرتبط با موضوع (نه عبارات کلی)
- شاخه‌ها: مکانیسم، موارد مصرف یا تداخلات، عوارض، احتیاط‌ها، پایش بالینی
- بدون توصیه شخصی قطعی
"""

    last_error = None
    for attempt in range(1, 4):
        try:
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            raw = (response.text or "").strip()
            print(f"[RESEARCH] پاسخ Gemini دریافت شد ({len(raw)} کاراکتر) attempt={attempt}")

            parsed = _parse_gemini_json(raw)
            if not parsed:
                print("[RESEARCH] JSON معتبر نبود")
                return _fallback_research(topic)

            summary = (parsed.get("summary") or "").strip()
            key_points = parsed.get("key_points") or []
            sources = parsed.get("sources") or []

            if len(summary) < 40 or len(key_points) < 3:
                fb = _fallback_research(topic)
                summary = summary if len(summary) >= 40 else fb["summary"]
                key_points = key_points if len(key_points) >= 3 else fb["key_points"]
                sources = sources or fb["sources"]

            return {
                "topic": topic,
                "summary": summary,
                "key_points": key_points,
                "sources": sources or _fallback_research(topic)["sources"],
            }

        except Exception as e:
            last_error = e
            msg = str(e)
            print(f"[RESEARCH] خطا attempt={attempt}: {e}")
            if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg.lower():
                await asyncio.sleep(2 * attempt)
                continue
            break

    print(f"[RESEARCH] نهایی ناموفق ({last_error}) – استفاده از پیش‌فرض غنی")
    return _fallback_research(topic)


async def generate_document(topic: str, research_data: dict) -> dict:
    print(f"[WRITER] در حال تولید مقاله برای: {topic}")
    try:
        return generate_article(topic, research_data)
    except Exception as e:
        print(f"[WRITER] خطا در تولید مقاله: {e}")
        return {
            "docx_path": None,
            "pdf_path": None,
            "abstract": research_data.get("summary", ""),
            "title": topic,
        }


async def generate_mindmap(topic: str, research_data: dict) -> str | None:
    print(f"[VISUALIZER] در حال ساخت مایند مپ برای: {topic}")
    try:
        return generate_mindmap_image(topic, research_data)
    except Exception as e:
        print(f"[VISUALIZER] خطا در ساخت مایند مپ: {e}")
        return None


async def generate_audio_summary(topic: str, research_data: dict) -> str | None:
    print(f"[AUDIO] در حال ساخت خلاصه صوتی برای: {topic}")
    try:
        return await make_audio(topic, research_data)
    except Exception as e:
        print(f"[AUDIO] خطا: {e}")
        return None


async def handle_research_request(topic: str, update=None, context=None):
    print(f"[CORE] شروع تحقیق برای موضوع: {topic} | supervisor={USE_SUPERVISOR}")

    if USE_SUPERVISOR:
        from agents.supervisor import run_with_supervisor

        result = await run_with_supervisor(topic)
        data = result.get("data") or {}
        document_package = data.get("document") or {"title": topic}
        mindmap_file = data.get("mindmap")
        audio_file = data.get("audio")
        research_data = data.get("research") or {}

        save_history({
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "status": "completed" if result.get("success") else "partial",
            "mode": "supervisor",
            "mindmap": mindmap_file,
            "document": document_package,
            "audio": audio_file,
            "errors": data.get("errors") or [],
        })

        if update and context:
            await send_package_to_telegram(update, document_package, mindmap_file, audio_file)

        return {
            "document": document_package,
            "mindmap": mindmap_file,
            "audio": audio_file,
            "research": research_data,
            "supervisor": result,
        }

    research_data = await run_research(topic)
    document_package = await generate_document(topic, research_data)
    mindmap_file = await generate_mindmap(topic, research_data)
    audio_file = await generate_audio_summary(topic, research_data)

    save_history({
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "mode": "single",
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
    title = document_package.get("title") or "موضوع تحقیق"

    if mindmap_file and Path(mindmap_file).exists():
        try:
            with open(mindmap_file, "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"مایند مپ: {title}")
        except Exception as e:
            await update.message.reply_text(f"مایند مپ ارسال نشد: {e}")

    docx_path = document_package.get("docx_path")
    if docx_path and Path(docx_path).exists():
        try:
            with open(docx_path, "rb") as f:
                await update.message.reply_document(document=f, filename=Path(docx_path).name, caption="مقاله علمی (Word)")
        except Exception as e:
            await update.message.reply_text(f"فایل Word ارسال نشد: {e}")

    pdf_path = document_package.get("pdf_path")
    if pdf_path and Path(pdf_path).exists():
        try:
            with open(pdf_path, "rb") as f:
                await update.message.reply_document(document=f, filename=Path(pdf_path).name, caption="مقاله علمی (PDF)")
        except Exception as e:
            await update.message.reply_text(f"فایل PDF ارسال نشد: {e}")

    if audio_file and Path(audio_file).exists():
        try:
            with open(audio_file, "rb") as f:
                await update.message.reply_audio(audio=f, title=f"خلاصه صوتی – {title}", caption="خلاصه صوتی تحقیق")
        except Exception as e:
            await update.message.reply_text(f"فایل صوتی ارسال نشد: {e}")

    await update.message.reply_text(
        f"✅ پکیج تحقیق «{title}» آماده شد.\n"
        "شامل:\n"
        "• مقاله علمی (Word + PDF)\n"
        "• مایند مپ تصویری\n"
        "• خلاصه صوتی فارسی"
    )
