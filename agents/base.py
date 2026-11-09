"""
base.py – رابط مشترک همه ایجنت‌ها
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    """خروجی استاندارد هر ایجنت"""
    success: bool
    agent_name: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "agent_name": self.agent_name,
            "data": self.data,
            "error": self.error,
        }


class BaseAgent(ABC):
    """کلاس پایه همه ایجنت‌ها"""

    name: str = "base"

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> AgentResult:
        """
        اجرای وظیفه ایجنت.
        context شامل موضوع و خروجی ایجنت‌های قبلی است.
        """
        raise NotImplementedError
