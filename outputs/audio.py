"""
audio.py – خلاصه صوتی با جزئیات بیشتر و تلفظ واضح‌تر
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import edge_tts

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# صدای مردانه رسمی معمولاً برای محتوای علمی پایدارتر است
DEFAULT_VOICE = "fa-IR-FaridNeural"
FALLBACK_VOICE = "fa-IR-DilaraNeural"
# کمی کندتر برای وضوح بیشتر
SPEECH_RATE = "-12%"
SPEECH_PITCH = "-2Hz"


def _safe_filename(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s\-آ-یA-Za-z0-9]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:max_len] or "audio_summary"


def _clean_spoken(text: str) -> str:
    """متن را برای گفتار روان‌تر می‌کند."""
    t = str(text or "").strip()
    t = t.replace("/", " یا ")
    t = t.replace("&", " و ")
    t = t.replace("–", " ")
    t = t.replace("—", " ")
    t = re.sub(r"\s+", " ", t)
    return t


def build_narration_script(topic: str, research_data: dict | None = None) -> str:
    data = research_data or {}
    summary = _clean_spoken(data.get("summary") or "")
    key_points = data.get("key_points") or []

    parts: list[str] = []
    parts.append(f"این یک خلاصه علمی کاربردی درباره { _clean_spoken(topic) } است.")

    if summary:
        if not summary.endswith((".", "؟", "!")):
            summary += "."
        parts.append(summary)
    else:
        parts.append(
            f"در این مرور، مکانیسم اثر، موارد مصرف، عوارض، تداخلات مهم و نکات پایش مرتبط با "
            f"{ _clean_spoken(topic) } بررسی می‌شود."
        )

    if key_points:
        parts.append("در ادامه، نکات اصلی را با جزئیات کوتاه مرور می‌کنیم.")
        for i, kp in enumerate(key_points[:5], 1):
            if isinstance(kp, dict):
                title = _clean_spoken(kp.get("title") or f"بخش {i}")
                children = [_clean_spoken(c) for c in (kp.get("children") or []) if str(c).strip()]
                # جمله کامل به‌جای فهرست خشک
                if children:
                    detail = "، ".join(children[:4])
                    parts.append(
                        f"در بخش {title}، موارد مهم عبارت‌اند از: {detail}. "
                        f"این نکات باید در ارزیابی بیمار و انتخاب رژیم درمانی مدنظر قرار گیرند."
                    )
                else:
                    parts.append(f"بخش {title} از نظر بالینی اهمیت دارد و نیازمند توجه دقیق است.")
            else:
                parts.append(_clean_spoken(str(kp)) + ".")
    else:
        parts.append(
            "به‌طور کلی باید به مکانیسم اثر، اندیکاسیون دقیق، عوارض شایع و جدی، "
            "تداخلات دارویی مهم، تنظیم دوز در نارسایی کلیه یا کبد، و آموزش بیمار توجه شود."
        )

    parts.append(
        "در عمل، تصمیم نهایی باید بر اساس شرایط هر بیمار، آزمایش‌های مرتبط، "
        "و آخرین دستورالعمل‌های معتبر گرفته شود. "
        "این خلاصه فقط جنبه آموزشی دارد و جایگزین نظر متخصص نیست."
    )

    script = " ".join(parts)
    script = re.sub(r"\s+", " ", script).strip()
    return script


async def _synthesize(text: str, output_path: Path, voice: str) -> Path:
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=SPEECH_RATE,
        pitch=SPEECH_PITCH,
    )
    await communicate.save(str(output_path))
    return output_path


async def generate_audio_summary(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
    voice: str = DEFAULT_VOICE,
) -> str | None:
    script = build_narration_script(topic, research_data)
    print(f"[AUDIO] نریشن ({len(script)} کاراکتر): {script[:200]}...")

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
