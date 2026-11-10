"""
audio.py – خلاصه صوتی فارسی با محتوای کامل تحقیق (نه فقط عنوان)
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import edge_tts

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICE = "fa-IR-DilaraNeural"
FALLBACK_VOICE = "fa-IR-FaridNeural"


def _safe_filename(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s\-آ-یA-Za-z0-9]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:max_len] or "audio_summary"


def build_narration_script(topic: str, research_data: dict | None = None) -> str:
    """
    متن نریشن ۱٫۵ تا ۳ دقیقه‌ای با جزئیات واقعی تحقیق.
    """
    data = research_data or {}
    summary = (data.get("summary") or "").strip()
    key_points = data.get("key_points") or []
    sources = data.get("sources") or []

    parts: list[str] = []
    parts.append(f"سلام. این یک خلاصه علمی درباره موضوع {topic} است.")

    if summary:
        parts.append(summary if summary.endswith((".", "۔", "!", "؟")) else summary + ".")
    else:
        parts.append(
            f"در این بررسی، جنبه‌های بالینی و داروسازی موضوع {topic} "
            f"شامل مکانیسم، موارد مصرف، عوارض، تداخلات و نکات پایش مرور می‌شود."
        )

    if key_points:
        parts.append("اکنون نکات اصلی را مرور می‌کنیم.")
        for i, kp in enumerate(key_points[:6], 1):
            if isinstance(kp, dict):
                title = str(kp.get("title") or f"نکته {i}").strip()
                children = [str(c).strip() for c in (kp.get("children") or []) if str(c).strip()]
                if children:
                    child_text = "؛ ".join(children[:4])
                    parts.append(f"نکته {i}. {title}. شامل این موارد: {child_text}.")
                else:
                    parts.append(f"نکته {i}. {title}.")
            else:
                parts.append(f"نکته {i}. {str(kp).strip()}.")
    else:
        parts.append(
            "به‌طور کلی باید به مکانیسم اثر، اندیکاسیون، عوارض شایع و جدی، "
            "تداخلات مهم دارویی، و نحوه پایش بیمار توجه شود."
        )

    parts.append(
        "در عمل بالینی، تصمیم‌گیری باید بر اساس شرایط هر بیمار، "
        "آخرین دستورالعمل‌ها و مشورت تیم درمان انجام شود."
    )

    if sources:
        parts.append("منابع این خلاصه شامل منابع معتبر دارویی و مقالات علمی است.")

    parts.append(
        "توجه: این محتوا صرفاً جنبه آموزشی و کمک‌تصمیم دارد "
        "و جایگزین نظر متخصص یا دستورالعمل رسمی نیست. پایان خلاصه."
    )

    script = " ".join(parts)
    # حذف فاصله‌های تکراری
    script = re.sub(r"\s+", " ", script).strip()
    return script


async def _synthesize(text: str, output_path: Path, voice: str) -> Path:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


async def generate_audio_summary(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
    voice: str = DEFAULT_VOICE,
) -> str | None:
    script = build_narration_script(topic, research_data)
    print(f"[AUDIO] نریشن ({len(script)} کاراکتر): {script[:180]}...")

    if len(script) < 80:
        print("[AUDIO] هشدار: متن نریشن خیلی کوتاه است")

    if not output_name:
        output_name = f"audio_{_safe_filename(topic)}.mp3"

    out_path = OUTPUT_DIR / output_name

    try:
        await _synthesize(script, out_path, voice=voice)
        print(f"[AUDIO] → {out_path}")
        return str(out_path)
    except Exception as e:
        print(f"[AUDIO] خطا با {voice}: {e}")
        if voice != FALLBACK_VOICE:
            try:
                await _synthesize(script, out_path, voice=FALLBACK_VOICE)
                print(f"[AUDIO] با صدای جایگزین → {out_path}")
                return str(out_path)
            except Exception as e2:
                print(f"[AUDIO] خطای نهایی: {e2}")
        return None


def generate_audio_summary_sync(topic: str, research_data: dict | None = None) -> str | None:
    return asyncio.run(generate_audio_summary(topic, research_data))
