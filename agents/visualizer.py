"""
VisualizerAgent – مسئول ساخت مایند مپ تصویری
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentResult
from outputs.mindmap import generate_mindmap_image


class VisualizerAgent(BaseAgent):
    name = "visualizer"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        topic = (context.get("topic") or "").strip()
        research = context.get("research") or {}

        if not topic:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error="موضوع برای مایند مپ خالی است",
            )

        try:
            path = generate_mindmap_image(topic, research)
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"mindmap": path},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error=str(e),
            )
