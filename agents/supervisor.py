"""
SupervisorAgent – سرپرست مولتی‌ایجنت

وظیفه:
1. دریافت موضوع
2. تقسیم کار بین ایجنت‌ها
3. جمع‌آوری نتایج
4. برگرداندن پکیج نهایی
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentResult
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.visualizer import VisualizerAgent
from agents.audio_agent import AudioAgent


class SupervisorAgent(BaseAgent):
    name = "supervisor"

    def __init__(self, agents: list[BaseAgent] | None = None):
        # ترتیب اجرای پیش‌فرض
        self.agents = agents or [
            ResearcherAgent(),
            WriterAgent(),
            VisualizerAgent(),
            AudioAgent(),
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
                # فعلاً ادامه می‌دهیم تا بقیه خروجی‌ها هم تولید شوند
                continue

            # ادغام خروجی ایجنت در context مشترک
            shared.update(result.data or {})

        package = {
            "topic": topic,
            "research": shared.get("research"),
            "document": shared.get("document"),
            "mindmap": shared.get("mindmap"),
            "audio": shared.get("audio"),
            "agent_results": results,
            "errors": errors,
        }

        success = len(errors) == 0
        print(f"[SUPERVISOR] پایان کار | موفقیت کامل: {success}")

        return AgentResult(
            success=success or bool(shared.get("document") or shared.get("mindmap")),
            agent_name=self.name,
            data=package,
            error="; ".join(errors) if errors else None,
        )


async def run_with_supervisor(topic: str) -> dict[str, Any]:
    """تابع کمکی برای اجرای کامل تحت سرپرست"""
    supervisor = SupervisorAgent()
    result = await supervisor.run({"topic": topic})
    return result.to_dict()
