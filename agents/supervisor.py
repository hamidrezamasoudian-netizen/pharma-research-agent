"""
SupervisorAgent – سرپرست مولتی‌ایجنت

وظیفه:
1. دریافت موضوع
2. تقسیم کار بین ایجنت‌ها
3. جمع‌آوری نتایج
4. بازبینی نهایی
5. برگرداندن پکیج نهایی
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentResult
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.visualizer import VisualizerAgent
from agents.audio_agent import AudioAgent
from agents.reviewer import ReviewerAgent


class SupervisorAgent(BaseAgent):
    name = "supervisor"

    def __init__(self, agents: list[BaseAgent] | None = None):
        # ترتیب اجرای پیش‌فرض
        self.agents = agents or [
            ResearcherAgent(),
            WriterAgent(),
            VisualizerAgent(),
            AudioAgent(),
            ReviewerAgent(),  # بازبینی در انتها
        ]

    async def run(self, context: dict[str, Any]) -> AgentResult:
        topic = (context.get("topic") or "").strip()
        if not topic:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error="موضوع خالی است",
            )

        shared: dict[str, Any] = {"topic": topic}
        results: list[dict[str, Any]] = []
        errors: list[str] = []

        print(f"[SUPERVISOR] شروع پروژه برای موضوع: {topic}")

        for agent in self.agents:
            print(f"[SUPERVISOR] اجرای ایجنت: {agent.name}")
            result = await agent.run(shared)
            results.append(result.to_dict())

            if not result.success:
                errors.append(f"{agent.name}: {result.error}")
                print(f"[SUPERVISOR] خطا در {agent.name}: {result.error}")
                continue

            shared.update(result.data or {})

        review = shared.get("review") or {}
        package = {
            "topic": topic,
            "research": shared.get("research"),
            "document": shared.get("document"),
            "mindmap": shared.get("mindmap"),
            "audio": shared.get("audio"),
            "review": review,
            "agent_results": results,
            "errors": errors,
        }

        # موفقیت کلی: اگر خروجی اصلی آمده باشد
        success = bool(shared.get("document") or shared.get("mindmap"))
        if review and review.get("approved") is False:
            # بازبینی ناموفق مانع کل کار نمی‌شود، فقط در گزارش می‌آید
            print("[SUPERVISOR] بازبین هشدار داده است")

        print(f"[SUPERVISOR] پایان کار | موفقیت: {success} | score={review.get('score')}")

        return AgentResult(
            success=success,
            agent_name=self.name,
            data=package,
            error="; ".join(errors) if errors else None,
        )


async def run_with_supervisor(topic: str) -> dict[str, Any]:
    """تابع کمکی برای اجرای کامل تحت سرپرست"""
    supervisor = SupervisorAgent()
    result = await supervisor.run({"topic": topic})
    return result.to_dict()
