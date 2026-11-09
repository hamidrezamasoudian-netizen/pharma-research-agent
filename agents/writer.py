"""
WriterAgent – مسئول تولید مقاله علمی DOCX/PDF
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentResult
from outputs.document import generate_article


class WriterAgent(BaseAgent):
    name = "writer"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        topic = (context.get("topic") or "").strip()
        research = context.get("research") or {}

        if not topic:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error="موضوع برای نگارش خالی است",
            )

        try:
            package = generate_article(topic, research)
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"document": package},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error=str(e),
            )
