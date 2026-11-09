"""
agents package

هر ایجنت یک مسئولیت مشخص دارد.
Supervisor آن‌ها را هماهنگ می‌کند.
"""

from .base import BaseAgent, AgentResult
from .researcher import ResearcherAgent
from .writer import WriterAgent
from .visualizer import VisualizerAgent
from .audio_agent import AudioAgent
from .supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "ResearcherAgent",
    "WriterAgent",
    "VisualizerAgent",
    "AudioAgent",
    "SupervisorAgent",
]
