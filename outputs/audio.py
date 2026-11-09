"""
audio.py – تولید خلاصه صوتی فارسی از موضوع تحقیق

از edge-tts برای نریشن فارسی استفاده می‌کند.
این ماژول در آینده می‌تواند به Audio Agent مستقل تبدیل شود.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import edge_tts

OUTPUT_DIR = Path("outputs/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# صدای فارسی با کیفیت مناسب
DEFAULT_VOICE = "fa-IR-DilaraNeural"  # صدای زنانه طبیعی
FALLBACK_VOICE = "fa-IR-FaridNeural"  # صدای مردانه


def _safe_filename(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s\-آ-ی]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:max_len] or "audio_summary"


def build_narration_script(topic: str, research_data: dict | None = None) -> str:
    """
    متن نریشن کوتاه و روان برای خلاصه صوتی می‌سازد.
    هدف: حدود ۱٫۵ تا ۳ دقیقه صحبت.
    """
    data = research_data or {}
    summary = data.get("summary") or f"بررسی علمی موضوع {topic}"
    key_points = data.get("key_points") or []

    lines = [
        f"خلاصه تحقیق در مورد {topic}.",
        summary.strip() + ".",
    ]

    if key_points:
        lines.append("نکات اصلی این بررسی عبارتند از:")
        for i, kp in enumerate(key_points[:5], 1):
            if isinstance(kp, dict):
                title = kp.get("title", "")
                children = kp.get("children") or []
                child_text = "، ".join(str(c) for c in children[:3])
                if child_text:
                    lines.append(f"{i}. {title}: {child_text}.")
                else:
                    lines.append(f"{i}. {title}.")
            else:
                lines.append(f"{i}. {kp}.")

    lines.append(
        "توجه داشته باشید که این خلاصه صرفاً جنبه آموزشی و کمک‌تصمیم دارد "
        "و جایگزین نظر متخصص و دستورالعمل‌های رسمی نیست."
    )
    lines.append("پایان خلاصه.")

    return " ".join(lines)


async def _synthesize(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


async def generate_audio_summary(
    topic: str,
    research_data: dict | None = None,
    output_name: str | None = None,
    voice: str = DEFAULT_VOICE,
) -> str | None:
    """
    خلاصه صوتی فارسی تولید می‌کند و مسیر فایل را برمی‌گرداند.
    """
    script = build_narration_script(topic, research_data)
    print(f"[AUDIO] متن نریشن ({len(script)} کاراکتر): {script[:120]}...")

    if not output_name:
        output_name = f"audio_{_safe_filename(topic)}.mp3"

    out_path = OUTPUT_DIR / output_name

    try:
        await _synthesize(script, out_path, voice=voice)
        print(f"[AUDIO] ذخیره شد → {out_path}")
        return str(out_path)
    except Exception as e:
        print(f"[AUDIO] خطا با صدای {voice}: {e}")
        # تلاش با صدای جایگزین
        if voice != FALLBACK_VOICE:
            try:
                await _synthesize(script, out_path, voice=FALLBACK_VOICE)
                print(f"[AUDIO] با صدای جایگزین ذخیره شد → {out_path}")
                return str(out_path)
            except Exception as e2:
                print(f"[AUDIO] خطای نهایی: {e2}")
        return None


def generate_audio_summary_sync(topic: str, research_data: dict | None = None) -> str | None:
    """نسخه همگام برای فراخوانی ساده."""
    return asyncio.run(generate_audio_summary(topic, research_data))


if __name__ == "__main__":
    path = generate_audio_summary_sync(
        "تداخلات دارویی متفورمین با داروهای قلبی",
        {
            "summary": "متفورمین داروی خط اول دیابت نوع دو است و تداخلات مهمی با برخی داروهای قلبی دارد.",
            "key_points": [
                {"title": "مکانیسم", "children": ["کاهش گلوکونئوژنز", "حساسیت انسولین"]},
                {"title": "تداخلات", "children": ["مهارکننده‌های ACE", "دیورتیک‌ها"]},
            ],
        },
    )
    print("نتیجه تست صوت:", path)
