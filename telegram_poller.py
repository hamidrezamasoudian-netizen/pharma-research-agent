"""
telegram_poller.py

هر چند دقیقه یک‌بار (توسط GitHub Actions) اجرا می‌شود:
1) پیام‌های جدید تلگرام را می‌گیرد
2) فقط پیام‌های ادمین را می‌پذیرد
3) موضوع را به ایجنت می‌دهد
4) نتیجه را به همان چت برمی‌گرداند
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import requests

from agent_core import handle_research_request

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()
STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)
LAST_UPDATE_FILE = STATE_DIR / "last_update_id.txt"
API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def get_last_update_id() -> int:
    if LAST_UPDATE_FILE.exists():
        try:
            return int(LAST_UPDATE_FILE.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            return 0
    return 0


def save_last_update_id(update_id: int) -> None:
    LAST_UPDATE_FILE.write_text(str(update_id), encoding="utf-8")


def tg_api(method: str, **params):
    r = requests.post(f"{API}/{method}", data=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def send_message(chat_id: str | int, text: str):
    return tg_api("sendMessage", chat_id=chat_id, text=text)


def send_document(chat_id: str | int, path: str, caption: str = ""):
    with open(path, "rb") as f:
        r = requests.post(
            f"{API}/sendDocument",
            data={"chat_id": chat_id, "caption": caption},
            files={"document": f},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()


def send_photo(chat_id: str | int, path: str, caption: str = ""):
    with open(path, "rb") as f:
        r = requests.post(
            f"{API}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption},
            files={"photo": f},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()


def send_audio(chat_id: str | int, path: str, caption: str = ""):
    with open(path, "rb") as f:
        r = requests.post(
            f"{API}/sendAudio",
            data={"chat_id": chat_id, "caption": caption},
            files={"audio": f},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()


def fetch_updates(offset: int) -> list[dict]:
    return tg_api(
        "getUpdates",
        offset=offset,
        timeout=0,
        allowed_updates=json.dumps(["message"]),
    )


def is_admin(user_id: str | int) -> bool:
    if not TELEGRAM_ADMIN_ID:
        return True
    return str(user_id) == str(TELEGRAM_ADMIN_ID)


async def process_topic(chat_id: str | int, topic: str):
    send_message(chat_id, f"موضوع دریافت شد:\n«{topic}»\n\nدر حال تحقیق...")

    # برای جلوگیری از وابستگی به آبجکت Update تلگرام، مستقیم پکیج را می‌سازیم
    result = await handle_research_request(topic, update=None, context=None)

    document = (result or {}).get("document") or {}
    mindmap = (result or {}).get("mindmap")
    audio = (result or {}).get("audio")
    title = document.get("title") or topic

    if mindmap and Path(mindmap).exists():
        try:
            send_photo(chat_id, mindmap, caption=f"مایند مپ: {title}")
        except Exception as e:
            send_message(chat_id, f"مایند مپ ساخته شد اما ارسال نشد: {e}")

    docx_path = document.get("docx_path")
    if docx_path and Path(docx_path).exists():
        try:
            send_document(chat_id, docx_path, caption="مقاله علمی (Word)")
        except Exception as e:
            send_message(chat_id, f"فایل Word ارسال نشد: {e}")

    pdf_path = document.get("pdf_path")
    if pdf_path and Path(pdf_path).exists():
        try:
            send_document(chat_id, pdf_path, caption="مقاله علمی (PDF)")
        except Exception as e:
            send_message(chat_id, f"فایل PDF ارسال نشد: {e}")

    if audio and Path(audio).exists():
        try:
            send_audio(chat_id, audio, caption="خلاصه صوتی تحقیق")
        except Exception as e:
            send_message(chat_id, f"فایل صوتی ارسال نشد: {e}")

    send_message(
        chat_id,
        f"✅ پکیج تحقیق «{title}» آماده شد.\n"
        "شامل: مقاله (Word/PDF) + مایند مپ + خلاصه صوتی",
    )


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN تنظیم نشده است")

    last_id = get_last_update_id()
    updates = fetch_updates(offset=last_id + 1 if last_id else 0)

    if not updates:
        print("[POLLER] پیام جدیدی نیست")
        return

    max_id = last_id
    for upd in updates:
        update_id = int(upd.get("update_id", 0))
        max_id = max(max_id, update_id)

        msg = upd.get("message") or {}
        text = (msg.get("text") or "").strip()
        chat = msg.get("chat") or {}
        user = msg.get("from") or {}
        chat_id = chat.get("id")
        user_id = user.get("id")

        if not text or chat_id is None:
            continue

        if text.startswith("/start"):
            send_message(chat_id, "سلام! موضوع تحقیق را بفرستید تا پکیج کامل را آماده کنم.")
            continue

        if text.startswith("/"):
            continue

        if not is_admin(user_id):
            send_message(chat_id, "دسترسی فقط برای ادمین فعال است.")
            continue

        if len(text) < 5:
            send_message(chat_id, "لطفاً موضوع دقیق‌تری ارسال کنید.")
            continue

        print(f"[POLLER] موضوع جدید از {user_id}: {text}")
        try:
            asyncio.run(process_topic(chat_id, text))
        except Exception as e:
            print(f"[POLLER] خطا: {e}")
            try:
                send_message(chat_id, f"خطا در انجام تحقیق: {e}")
            except Exception:
                pass

    if max_id > last_id:
        save_last_update_id(max_id)
        print(f"[POLLER] last_update_id → {max_id}")


if __name__ == "__main__":
    main()
