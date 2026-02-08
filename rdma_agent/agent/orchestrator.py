"""
Agent Orchestrator - The core brain of the RDMA Agent system.
Coordinates between issue detection, RAG knowledge retrieval,
LLM analysis, skill execution, and human escalation.
"""

import asyncio
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from .llm_client import LLMClient
from .prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_PROMPT_TEMPLATE,
    ACTION_RESULT_PROMPT_TEMPLATE,
    FINAL_REPORT_PROMPT,
)
from ..rag.knowledge_manager import KnowledgeManager
from ..skills.registry import SkillRegistry
from ..collectors.monitor import DetectedIssue

logger = logging.getLogger(__name__)


@dataclass
class InvestigationStep:
    """Record of a single investigation step."""
    step_number: int
    skill_name: str
    params: dict
    output: str
    success: bool
    timestamp: str = ""


@dataclass
class Investigation:
    """Full investigation record for a detected issue."""
    issue: DetectedIssue = None
    hypothesis: str = ""
    confidence: float = 0.0
    action_plan: list = field(default_factory=list)
    steps_completed: list = field(default_factory=list)
    findings: str = ""
    resolution: Optional[str] = None
    escalated: bool = False
    final_report: str = ""
    started_at: str = ""
    completed_at: str = ""
    status: str = "pending"  # pending, in_progress, resolved, escalated, failed


class AgentOrchestrator:
    """
    Orchestrates the full RDMA issue investigation lifecycle:
    1. Receive detected issue
    2. Query RAG for relevant knowledge
    3. Ask LLM to analyze and create action plan
    4. Execute action plan steps using skills
    5. Feed results back to LLM for updated analysis
    6. Repeat until resolved or escalation needed
    """

    def __init__(
        self,
        llm: LLMClient,
        knowledge: KnowledgeManager,
        skills: SkillRegistry,
        max_retries: int = 3,
        dataset_id: str = "",
        on_alarm=None,  # async callback for escalation
    ):
        self.llm = llm
        self.knowledge = knowledge
        self.skills = skills
        self.max_retries = max_retries
        self.dataset_id = dataset_id
        self.on_alarm = on_alarm
        self.investigations: dict[str, Investigation] = {}

    async def investigate(self, issue: DetectedIssue) -> Investigation:
        """
        Run a full investigation for a detected issue.
        This is the main entry point called by the monitor.
        """
        investigation = Investigation(
            issue=issue,
            started_at=datetime.utcnow().isoformat(),
            status="in_progress",
        )
        self.investigations[issue.issue_id] = investigation

        logger.info("Starting investigation for %s: %s", issue.issue_id, issue.summary)

        try:
            # Step 1: Query RAG for relevant knowledge
            rag_context = await self._get_rag_context(issue)

            # Step 2: Initial LLM analysis
            analysis = await self._initial_analysis(issue, rag_context)
            if not analysis:
                investigation.status = "failed"
                investigation.escalated = True
                await self._escalate(investigation, "LLM analysis failed")
                return investigation

            investigation.hypothesis = analysis.get("root_cause_hypothesis", "Unknown")
            investigation.confidence = analysis.get("confidence", 0.0)
            investigation.action_plan = analysis.get("action_plan", [])

            # Step 3: Execute action plan
            if analysis.get("escalation_needed"):
                investigation.status = "escalated"
                investigation.escalated = True
                await self._escalate(investigation, "LLM recommended immediate escalation")
                return investigation

            await self._execute_action_plan(investigation, rag_context)

            # Step 4: Generate final report
            investigation.final_report = await self._generate_report(investigation)
            investigation.completed_at = datetime.utcnow().isoformat()

            if investigation.resolution:
                investigation.status = "resolved"
            elif investigation.escalated:
                investigation.status = "escalated"
            else:
                investigation.status = "failed"
                await self._escalate(investigation, "All action plan steps exhausted without resolution")

        except Exception as e:
            logger.error("Investigation failed: %s", e, exc_info=True)
            investigation.status = "failed"
            investigation.escalated = True
            await self._escalate(investigation, f"Investigation error: {e}")

        return investigation

    async def _get_rag_context(self, issue: DetectedIssue) -> str:
        """Query the knowledge base for relevant RDMA troubleshooting knowledge."""
        query = f"RDMA troubleshooting: {issue.category} - {issue.summary}"
        try:
            results = await self.knowledge.query(query, self.dataset_id, top_k=5)
            if results:
                context_parts = []
                for i, r in enumerate(results, 1):
                    context_parts.append(f"[{i}] {r.get('text', '')}")
                return "\n\n".join(context_parts)
        except Exception as e:
            logger.warning("RAG query failed: %s", e)
        return "No relevant knowledge base entries found."

    async def _initial_analysis(self, issue: DetectedIssue, rag_context: str) -> Optional[dict]:
        """Ask the LLM to analyze the issue and produce an action plan."""
        # Prepare diagnostic data summary
        diag_data = json.dumps(issue.details, indent=2, default=str)

        # Get available skills for the LLM
        skills_desc = json.dumps(self.skills.get_llm_tool_definitions(), indent=2)

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            issue_summary=issue.summary,
            severity=issue.severity,
            category=issue.category,
            diagnostic_data=diag_data,
            rag_context=rag_context,
            available_skills=skills_desc,
        )

        try:
            response = await self.llm.analyze_with_context(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
            # Parse JSON from response
            return self._extract_json(response)
        except Exception as e:
            logger.error("LLM analysis failed: %s", e)
            return None

    async def _execute_action_plan(self, investigation: Investigation, rag_context: str):
        """Execute each step of the action plan, feeding results back to LLM."""
        plan = investigation.action_plan
        retry_count = 0

        for i, step in enumerate(plan):
            skill_name = step.get("skill", "")
            params = step.get("params", {})

            logger.info(
                "Executing step %d/%d: %s(%s)",
                i + 1, len(plan), skill_name, params,
            )

            # Execute the skill
            result = self.skills.execute(skill_name, params)
            inv_step = InvestigationStep(
                step_number=i + 1,
                skill_name=skill_name,
                params=params,
                output=result.get("output", ""),
                success=result.get("success", False),
                timestamp=datetime.utcnow().isoformat(),
            )
            investigation.steps_completed.append(inv_step)

            # Feed result back to LLM
            previous_results = "\n".join(
                f"Step {s.step_number}: {s.skill_name} -> {'OK' if s.success else 'FAILED'}"
                for s in investigation.steps_completed[:-1]
            )

            prompt = ACTION_RESULT_PROMPT_TEMPLATE.format(
                issue_summary=investigation.issue.summary,
                hypothesis=investigation.hypothesis,
                completed_steps=len(investigation.steps_completed),
                total_steps=len(plan),
                skill_name=skill_name,
                skill_params=json.dumps(params),
                skill_output=result.get("output", "")[:3000],
                previous_results=previous_results or "None",
                available_skills=json.dumps(self.skills.get_llm_tool_definitions(), indent=2),
            )

            try:
                response = await self.llm.analyze_with_context(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=prompt,
                    context=rag_context,
                )
                update = self._extract_json(response)
                if update:
                    investigation.hypothesis = update.get(
                        "updated_hypothesis", investigation.hypothesis
                    )
                    investigation.confidence = update.get(
                        "confidence", investigation.confidence
                    )
                    investigation.findings = update.get(
                        "findings_so_far", investigation.findings
                    )

                    # Check if resolved
                    if update.get("resolution"):
                        investigation.resolution = update["resolution"]
                        return

                    # Check if escalation needed
                    if update.get("escalation_needed"):
                        investigation.escalated = True
                        await self._escalate(
                            investigation,
                            update.get("findings_so_far", "LLM requested escalation"),
                        )
                        return

                    # Check if LLM wants a different next action
                    next_action = update.get("next_action")
                    if next_action and i < len(plan) - 1:
                        # Replace remaining plan with LLM's suggestion
                        plan[i + 1] = {
                            "step": i + 2,
                            "skill": next_action["skill"],
                            "params": next_action["params"],
                            "description": next_action.get("reason", ""),
                        }

            except Exception as e:
                logger.warning("LLM update failed at step %d: %s", i + 1, e)
                retry_count += 1
                if retry_count >= self.max_retries:
                    investigation.escalated = True
                    await self._escalate(investigation, f"Too many LLM failures: {e}")
                    return

    async def _generate_report(self, investigation: Investigation) -> str:
        """Generate a final investigation report."""
        inv_log = "\n".join(
            f"Step {s.step_number}: {s.skill_name}({s.params}) -> "
            f"{'OK' if s.success else 'FAILED'}\n  Output: {s.output[:500]}"
            for s in investigation.steps_completed
        )

        prompt = FINAL_REPORT_PROMPT.format(
            issue_summary=investigation.issue.summary,
            investigation_log=inv_log or "No steps executed",
            findings=investigation.findings or "No findings recorded",
        )

        try:
            return await self.llm.get_response_text([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
        except Exception as e:
            logger.error("Report generation failed: %s", e)
            return f"Report generation failed: {e}"

    async def _escalate(self, investigation: Investigation, reason: str):
        """Escalate to human operators."""
        investigation.escalated = True
        logger.critical(
            "ESCALATION for %s: %s", investigation.issue.issue_id, reason
        )
        if self.on_alarm:
            await self.on_alarm(investigation, reason)

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response text."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        import re
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"\{.*\}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if "```" in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue
        logger.warning("Could not extract JSON from LLM response")
        return None

    def get_investigation(self, issue_id: str) -> Optional[Investigation]:
        """Get investigation status by issue ID."""
        return self.investigations.get(issue_id)

    def list_investigations(self) -> list[dict]:
        """List all investigations with basic info."""
        return [
            {
                "issue_id": inv.issue.issue_id,
                "summary": inv.issue.summary,
                "status": inv.status,
                "severity": inv.issue.severity,
                "hypothesis": inv.hypothesis,
                "confidence": inv.confidence,
                "started_at": inv.started_at,
                "completed_at": inv.completed_at,
                "steps_completed": len(inv.steps_completed),
                "escalated": inv.escalated,
            }
            for inv in self.investigations.values()
        ]
