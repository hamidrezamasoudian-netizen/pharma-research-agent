"""
ResearcherAgent – مسئول تحقیق و استخراج ساختار علمی موضوع
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentResult
from agent_core import run_research


class ResearcherAgent(BaseAgent):
    name = "researcher"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        topic = (context.get("topic") or "").strip()
        if not topic:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error="موضوع تحقیق خالی است",
            )

        try:
            data = await run_research(topic)
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"research": data},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error=str(e),
            )
