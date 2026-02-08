"""
RDMA Agent - Main Application
Starts the FastAPI server, initializes all components, and begins monitoring.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config.settings import load_config
from .agent.llm_client import LLMClient
from .agent.orchestrator import AgentOrchestrator
from .agent.alarm import AlarmManager
from .rag.knowledge_manager import KnowledgeManager
from .skills.registry import SkillRegistry
from .skills.builtin_skills import register_builtin_skills
from .collectors.monitor import IssueMonitor
from .dify.workflow import DifyWorkflowManager
from .api.routes import router, set_dependencies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global references
_monitor_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and start all components."""
    global _monitor_task

    config = load_config()
    logger.info("Starting RDMA Agent System v1.0.0")

    # 1. Initialize LLM client
    llm = LLMClient(
        api_base=config.llm.api_base,
        api_key=config.llm.api_key,
        model_name=config.llm.model_name,
        max_tokens=config.llm.max_tokens,
        temperature=config.llm.temperature,
    )
    logger.info("LLM client initialized (%s)", config.llm.api_base)

    # 2. Initialize knowledge manager
    knowledge = KnowledgeManager(
        mode="dify" if config.dify.dataset_api_key else "local",
        dify_api_base=config.dify.api_base,
        dify_dataset_api_key=config.dify.dataset_api_key,
        embedding_api_base=config.embedding.api_base,
        embedding_api_key=config.embedding.api_key,
        embedding_model=config.embedding.model_name,
        rerank_api_base=config.rerank.api_base,
        rerank_api_key=config.rerank.api_key,
        rerank_model=config.rerank.model_name,
        rerank_top_n=config.rerank.top_n,
        chroma_persist_dir=os.path.join(config.data_dir, "chroma"),
    )
    logger.info("Knowledge manager initialized (mode=%s)", knowledge.mode)

    # 3. Initialize skill registry
    skills = SkillRegistry()
    register_builtin_skills(skills)
    logger.info("Skill registry initialized (%d skills)", len(skills.list_skills()))

    # 4. Initialize alarm manager
    alarm = AlarmManager(config.alarm)

    # 5. Initialize Dify workflow manager
    dify = DifyWorkflowManager(
        api_base=config.dify.api_base,
        api_key=config.dify.api_key,
        dataset_api_key=config.dify.dataset_api_key,
    )

    # 6. Initialize orchestrator
    orchestrator = AgentOrchestrator(
        llm=llm,
        knowledge=knowledge,
        skills=skills,
        max_retries=config.monitor.max_retry_actions,
        on_alarm=alarm.send_alarm,
    )
    logger.info("Agent orchestrator initialized")

    # 7. Initialize and start monitor
    async def on_issue(issue):
        logger.info("Auto-investigating issue: %s", issue.issue_id)
        await orchestrator.investigate(issue)

    monitor = IssueMonitor(
        poll_interval=config.monitor.poll_interval_seconds,
        on_issue_detected=on_issue,
    )

    # Set API dependencies
    set_dependencies(orchestrator, monitor, skills, knowledge, alarm, dify)

    # Start monitor in background
    _monitor_task = asyncio.create_task(monitor.start())
    logger.info("Issue monitor started (interval=%ds)", config.monitor.poll_interval_seconds)

    logger.info("RDMA Agent System ready on %s:%d", config.host, config.port)

    yield

    # Shutdown
    logger.info("Shutting down RDMA Agent System...")
    monitor.stop()
    if _monitor_task:
        _monitor_task.cancel()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="RDMA Network Issue Analysis Agent",
    description="RAG + Agent + LLM system for automatic RDMA issue detection and resolution",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router)

# Serve UI static files
ui_dir = os.path.join(os.path.dirname(__file__), "ui")
if os.path.isdir(ui_dir):
    app.mount("/static", StaticFiles(directory=ui_dir), name="static")


@app.get("/")
async def root():
    """Serve the UI dashboard."""
    index_path = os.path.join(ui_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "RDMA Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn

    config = load_config()
    uvicorn.run(
        "rdma_agent.app:app",
        host=config.host,
        port=config.port,
        reload=True,
    )
