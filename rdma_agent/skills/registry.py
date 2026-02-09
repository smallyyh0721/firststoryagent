"""
Skill Registry - Extensible framework for defining diagnostic skills.
Each skill is a callable that the agent can invoke to collect debug info
or perform remediation actions.
"""

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """
    A diagnostic/remediation skill that the agent can invoke.

    Attributes:
        name: Unique skill identifier (e.g., "check_rdma_counters")
        description: Human-readable description for the LLM to understand when to use it
        category: Grouping category (diagnostics, remediation, collection, analysis)
        command_template: Shell command template with {placeholders}
        parameters: List of parameter names the skill accepts
        requires_sudo: Whether the skill needs root privileges
        handler: Optional Python callable instead of shell command
    """
    name: str
    description: str
    category: str = "diagnostics"
    command_template: str = ""
    parameters: list = field(default_factory=list)
    requires_sudo: bool = False
    handler: Optional[Callable] = None
    risk_level: str = "safe"  # safe, moderate, dangerous

    def to_llm_description(self) -> dict:
        """Return a description suitable for LLM function-calling."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "risk_level": self.risk_level,
        }


class SkillRegistry:
    """
    Central registry for all diagnostic and remediation skills.
    Skills can be added at startup or dynamically at runtime.
    """

    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill):
        """Register a new skill."""
        if skill.name in self._skills:
            logger.warning("Overwriting existing skill: %s", skill.name)
        self._skills[skill.name] = skill
        logger.info("Registered skill: %s (%s)", skill.name, skill.category)

    def unregister(self, name: str):
        """Remove a skill."""
        self._skills.pop(name, None)

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self, category: Optional[str] = None) -> list[Skill]:
        """List all skills, optionally filtered by category."""
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return skills

    def get_llm_tool_definitions(self) -> list[dict]:
        """Return all skills as LLM tool definitions for function-calling."""
        return [s.to_llm_description() for s in self._skills.values()]

    def execute(self, name: str, params: Optional[dict] = None, timeout: int = 60) -> dict:
        """
        Execute a skill by name with given parameters.
        Returns {"success": bool, "output": str, "error": str}
        """
        skill = self._skills.get(name)
        if not skill:
            return {"success": False, "output": "", "error": f"Unknown skill: {name}"}

        params = params or {}

        try:
            # Use Python handler if available
            if skill.handler:
                result = skill.handler(**params)
                return {"success": True, "output": str(result), "error": ""}

            # Otherwise execute command template
            cmd = skill.command_template
            for key, val in params.items():
                # Basic sanitization - prevent injection
                safe_val = str(val).replace(";", "").replace("&", "").replace("|", "").replace("`", "")
                cmd = cmd.replace(f"{{{key}}}", safe_val)

            if skill.requires_sudo:
                cmd = f"sudo {cmd}"

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            output = result.stdout + result.stderr
            return {
                "success": result.returncode == 0,
                "output": output,
                "error": "" if result.returncode == 0 else f"Exit code: {result.returncode}",
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Skill {name} timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
