"""
AudioAgent – مسئول تولید خلاصه صوتی فارسی
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentResult
from outputs.audio import generate_audio_summary


class AudioAgent(BaseAgent):
    name = "audio"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        topic = (context.get("topic") or "").strip()
        research = context.get("research") or {}

        if not topic:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error="موضوع برای خلاصه صوتی خالی است",
            )

        try:
            path = await generate_audio_summary(topic, research)
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"audio": path},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                agent_name=self.name,
                error=str(e),
            )
