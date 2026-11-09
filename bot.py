"""
نقطه ورود تلگرام برای Pharma Research Agent
این فایل فقط رابط کاربری است و منطق اصلی در agent_core قرار دارد.
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from agent_core import handle_research_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ایجنت تحقیقات دارویی هستم.\n"
        "موضوع تحقیق خود را ارسال کنید تا پکیج کامل (مقاله + مایند مپ + صوت) را آماده کنم."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if TELEGRAM_ADMIN_ID and user_id != TELEGRAM_ADMIN_ID:
        await update.message.reply_text("دسترسی فقط برای ادمین فعال است.")
        return

    topic = update.message.text.strip()
    if not topic or len(topic) < 5:
        await update.message.reply_text("لطفاً موضوع دقیق‌تری ارسال کنید.")
        return

    await update.message.reply_text(f"موضوع دریافت شد:\n«{topic}»\n\nدر حال شروع تحقیق...")
    
    try:
        result = await handle_research_request(topic, update, context)
        if result:
            await update.message.reply_text("پکیج تحقیق آماده شد و ارسال گردید.")
    except Exception as e:
        logger.exception("خطا در پردازش تحقیق")
        await update.message.reply_text(f"خطا در انجام تحقیق: {e}")


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN تنظیم نشده است")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Pharma Research Agent is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
