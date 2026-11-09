# Pharma Research Agent

ایجنت تحقیقات دارویی هوشمند – نسخه تکی با معماری آماده برای ارتقا به مولتی‌ایجنت.

## هدف

موضوع تحقیق را از طریق تلگرام یا GitHub Actions ارسال کنید. ایجنت:

1. تحقیق علمی انجام می‌دهد (با Gemini در صورت وجود کلید)
2. مقاله کامل علمی (DOCX + PDF) تولید می‌کند
3. مایند مپ تصویری می‌سازد
4. خلاصه صوتی فارسی تولید می‌کند
5. پکیج را به تلگرام ارسال می‌کند (در صورت تنظیم توکن)

## معماری فعلی (تکی) و آماده برای مولتی‌ایجنت

```
Supervisor (آینده)
│
├── Research Agent      ← نسخه فعلی
├── Writer Agent
├── Visualizer Agent
├── Audio Agent
└── Reviewer Agent
```

## ساختار پروژه

```
pharma-research-agent/
├── bot.py                      # نقطه ورود تلگرام
├── agent_core.py               # هماهنگی اصلی
├── outputs/
│   ├── document.py             # مقاله DOCX + PDF
│   ├── mindmap.py              # مایند مپ تصویری
│   └── audio.py                # خلاصه صوتی
├── state/                      # تاریخچه تحقیقات
├── .github/workflows/
│   └── run-research.yml        # اجرای دستی / زمان‌بندی‌شده
├── requirements.txt
└── README.md
```

## وضعیت فعلی

- [x] ساختار پایه و معماری ماژولار
- [x] مایند مپ تصویری
- [x] مقاله علمی (Word + PDF)
- [x] خلاصه صوتی فارسی
- [x] تحقیق با Gemini (+ fallback)
- [x] Workflow گیت‌هاب
- [ ] ارتقا به مولتی‌ایجنت با Supervisor

## Secrets مورد نیاز (GitHub → Settings → Secrets)

| Secret | الزامی؟ | توضیح |
|--------|---------|--------|
| `GEMINI_API_KEY` | توصیه‌شده | برای تحقیق واقعی |
| `TELEGRAM_BOT_TOKEN` | برای ارسال | توکن ربات تلگرام |
| `TELEGRAM_ADMIN_ID` | اختیاری | محدود کردن دسترسی |
| `TELEGRAM_CHAT_ID` | اختیاری | چت مقصد |
| `GEMINI_MODEL` | اختیاری | پیش‌فرض: `gemini-2.0-flash` |

## اجرای دستی با Workflow

1. بروید به تب **Actions** در ریپو
2. workflow به نام **Run Pharma Research Agent** را انتخاب کنید
3. **Run workflow** بزنید و موضوع تحقیق را وارد کنید
4. پس از اتمام، فایل‌های تولیدشده در **Artifacts** قابل دانلود هستند

## اجرای محلی

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...
export TELEGRAM_BOT_TOKEN=...   # اختیاری
python bot.py
```

یا فقط یک تحقیق بدون تلگرام:

```bash
python -c "
import asyncio
from agent_core import handle_research_request
print(asyncio.run(handle_research_request('تداخلات متفورمین با داروهای قلبی')))
"
```

## افزودن ایجنت جدید (آینده)

1. ماژول جدید بسازید
2. در `agent_core.py` ثبت کنید
3. پس از ساخت Supervisor، آن را به عنوان یک Worker اضافه کنید

---
ساخته‌شده برای مدیریت هوشمند داروخانه و تحقیقات دارویی.
