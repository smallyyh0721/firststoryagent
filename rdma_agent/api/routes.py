"""
REST API routes for the RDMA Agent system.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["RDMA Agent"])

# These will be set by the main app during startup
_orchestrator = None
_monitor = None
_skills = None
_knowledge = None
_alarm = None
_dify = None


def set_dependencies(orchestrator, monitor, skills, knowledge, alarm, dify):
    global _orchestrator, _monitor, _skills, _knowledge, _alarm, _dify
    _orchestrator = orchestrator
    _monitor = monitor
    _skills = skills
    _knowledge = knowledge
    _alarm = alarm
    _dify = dify


# ── Health & Status ──────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "rdma-agent"}


@router.get("/status")
async def status():
    return {
        "monitor_running": _monitor._running if _monitor else False,
        "total_investigations": len(_orchestrator.investigations) if _orchestrator else 0,
        "registered_skills": len(_skills.list_skills()) if _skills else 0,
    }


# ── Manual Issue Detection ───────────────────────────────────────────

@router.post("/check")
async def run_manual_check(background_tasks: BackgroundTasks):
    """Run a manual detection cycle and investigate any issues found."""
    if not _monitor or not _orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    issues = await _monitor.run_manual_check()
    if not issues:
        return {"message": "No issues detected", "issues": []}

    # Start investigations in background
    for issue in issues:
        background_tasks.add_task(_orchestrator.investigate, issue)

    return {
        "message": f"Detected {len(issues)} issue(s), investigation started",
        "issues": [i.to_dict() for i in issues],
    }


# ── Investigations ───────────────────────────────────────────────────

@router.get("/investigations")
async def list_investigations():
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"investigations": _orchestrator.list_investigations()}


@router.get("/investigations/{issue_id}")
async def get_investigation(issue_id: str):
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    inv = _orchestrator.get_investigation(issue_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {
        "issue_id": inv.issue.issue_id,
        "summary": inv.issue.summary,
        "status": inv.status,
        "severity": inv.issue.severity,
        "hypothesis": inv.hypothesis,
        "confidence": inv.confidence,
        "findings": inv.findings,
        "resolution": inv.resolution,
        "escalated": inv.escalated,
        "final_report": inv.final_report,
        "steps": [
            {
                "step": s.step_number,
                "skill": s.skill_name,
                "params": s.params,
                "success": s.success,
                "output": s.output[:1000],
                "timestamp": s.timestamp,
            }
            for s in inv.steps_completed
        ],
        "started_at": inv.started_at,
        "completed_at": inv.completed_at,
    }


# ── Skills Management ────────────────────────────────────────────────

@router.get("/skills")
async def list_skills(category: Optional[str] = None):
    if not _skills:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    skills = _skills.list_skills(category)
    return {"skills": [s.to_llm_description() for s in skills]}


class SkillExecuteRequest(BaseModel):
    skill_name: str
    params: dict = {}


@router.post("/skills/execute")
async def execute_skill(req: SkillExecuteRequest):
    """Manually execute a skill (for testing/debugging)."""
    if not _skills:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    result = _skills.execute(req.skill_name, req.params)
    return result


class SkillRegisterRequest(BaseModel):
    name: str
    description: str
    category: str = "diagnostics"
    command_template: str = ""
    parameters: list = []
    requires_sudo: bool = False
    risk_level: str = "safe"


@router.post("/skills/register")
async def register_skill(req: SkillRegisterRequest):
    """Register a new skill at runtime."""
    if not _skills:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    from ..skills.registry import Skill
    skill = Skill(
        name=req.name,
        description=req.description,
        category=req.category,
        command_template=req.command_template,
        parameters=req.parameters,
        requires_sudo=req.requires_sudo,
        risk_level=req.risk_level,
    )
    _skills.register(skill)
    return {"message": f"Skill '{req.name}' registered", "skill": skill.to_llm_description()}


@router.delete("/skills/{skill_name}")
async def unregister_skill(skill_name: str):
    """Remove a skill."""
    if not _skills:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    _skills.unregister(skill_name)
    return {"message": f"Skill '{skill_name}' removed"}


# ── Knowledge Base ───────────────────────────────────────────────────

class KnowledgeQueryRequest(BaseModel):
    query: str
    dataset_id: str = ""
    top_k: int = 5


@router.post("/knowledge/query")
async def query_knowledge(req: KnowledgeQueryRequest):
    if not _knowledge:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    results = await _knowledge.query(req.query, req.dataset_id, req.top_k)
    return {"results": results}


class KnowledgeAddRequest(BaseModel):
    doc_id: str
    text: str
    metadata: dict = {}


@router.post("/knowledge/add")
async def add_knowledge(req: KnowledgeAddRequest):
    if not _knowledge:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    await _knowledge.add_document_local(req.doc_id, req.text, req.metadata)
    return {"message": f"Document '{req.doc_id}' added to knowledge base"}


# ── Alarms ───────────────────────────────────────────────────────────

@router.get("/alarms")
async def list_alarms():
    if not _alarm:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"alarms": _alarm.get_alarm_history()}


# ── Collect (Manual Snapshot) ────────────────────────────────────────

@router.get("/collect/rdma")
async def collect_rdma():
    """Collect and return a current RDMA snapshot."""
    from ..collectors.rdma_collector import RDMACollector
    import asyncio
    collector = RDMACollector()
    loop = asyncio.get_event_loop()
    snap = await loop.run_in_executor(None, collector.collect_all)
    return {
        "timestamp": snap.timestamp,
        "devices": snap.devices,
        "ports": snap.ports,
        "counters": snap.counters,
        "errors": snap.errors,
    }


@router.get("/collect/system")
async def collect_system():
    """Collect and return a current system snapshot."""
    from ..collectors.system_collector import SystemCollector
    import asyncio
    collector = SystemCollector()
    loop = asyncio.get_event_loop()
    snap = await loop.run_in_executor(None, collector.collect_all)
    return {
        "timestamp": snap.timestamp,
        "kernel_info": snap.kernel_info,
        "raw_outputs": {k: v[:2000] for k, v in snap.raw_outputs.items()},
    }


@router.get("/collect/switch")
async def collect_switch():
    """Collect and return a current switch/fabric snapshot."""
    from ..collectors.switch_collector import SwitchCollector
    import asyncio
    collector = SwitchCollector()
    loop = asyncio.get_event_loop()
    snap = await loop.run_in_executor(None, collector.collect_all)
    return {
        "timestamp": snap.timestamp,
        "switch_errors": snap.switch_errors,
        "raw_outputs": {k: v[:2000] for k, v in snap.raw_outputs.items()},
    }
