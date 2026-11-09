"""
ReviewerAgent – بازبینی کیفیت پکیج تحقیق

وظایف:
- بررسی کامل بودن خروجی‌ها
- بررسی حداقلی ساختار مقاله و یافته‌ها
- تولید گزارش بازبینی کوتاه
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.base import BaseAgent, AgentResult


class ReviewerAgent(BaseAgent):
    name = "reviewer"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        topic = (context.get("topic") or "").strip()
        research = context.get("research") or {}
        document = context.get("document") or {}
        mindmap = context.get("mindmap")
        audio = context.get("audio")

        issues: list[str] = []
        notes: list[str] = []

        if not topic:
            issues.append("موضوع خالی است")

        # بررسی تحقیق
        summary = (research.get("summary") or "").strip()
        key_points = research.get("key_points") or []
        sources = research.get("sources") or []

        if len(summary) < 40:
            issues.append("خلاصه تحقیق خیلی کوتاه است")
        else:
            notes.append("خلاصه تحقیق موجود است")

        if len(key_points) < 3:
            issues.append("تعداد شاخه‌های کلیدی کمتر از حد انتظار است")
        else:
            notes.append(f"تعداد شاخه‌های کلیدی: {len(key_points)}")

        if len(sources) < 1:
            issues.append("منبعی ثبت نشده است")
        else:
            notes.append(f"تعداد منابع: {len(sources)}")

        # بررسی مقاله
        docx_path = document.get("docx_path")
        pdf_path = document.get("pdf_path")

        if docx_path and Path(docx_path).exists():
            notes.append("فایل Word موجود است")
        else:
            issues.append("فایل Word موجود نیست")

        if pdf_path and Path(pdf_path).exists():
            notes.append("فایل PDF موجود است")
        else:
            issues.append("فایل PDF موجود نیست")

        # بررسی مایند مپ و صوت
        if mindmap and Path(str(mindmap)).exists():
            notes.append("مایند مپ موجود است")
        else:
            issues.append("مایند مپ موجود نیست")

        if audio and Path(str(audio)).exists():
            notes.append("خلاصه صوتی موجود است")
        else:
            issues.append("خلاصه صوتی موجود نیست")

        score = max(0, 100 - (len(issues) * 12))
        approved = len(issues) == 0

        report = {
            "approved": approved,
            "score": score,
            "issues": issues,
            "notes": notes,
            "summary": (
                "پکیج از نظر ساختاری تأیید شد."
                if approved
                else "پکیج نیاز به تکمیل دارد."
            ),
        }

        return AgentResult(
            success=True,  # خود بازبینی نباید کل pipeline را fail کند
            agent_name=self.name,
            data={"review": report},
            error="; ".join(issues) if issues else None,
        )
