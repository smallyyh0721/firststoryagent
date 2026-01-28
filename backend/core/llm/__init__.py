"""
LLM integration module
"""

from .client import LLMClient
from .prompts import STORY_GENERATION_PROMPT

__all__ = ["LLMClient", "STORY_GENERATION_PROMPT"]