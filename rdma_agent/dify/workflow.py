"""
Dify.ai Workflow Manager.
Manages Dify workflow definitions and provides integration between
the RDMA Agent and Dify's workflow engine.
"""

import logging
import json
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class DifyWorkflowManager:
    """
    Manages integration with Dify.ai platform.

    Dify provides:
    - Knowledge base management (RAG datasets)
    - Workflow orchestration (visual workflow builder)
    - LLM routing and model management
    - API endpoints for chat/completion

    This manager bridges our RDMA Agent with Dify's API.
    """

    def __init__(self, api_base: str, api_key: str, dataset_api_key: str = ""):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.dataset_api_key = dataset_api_key

    # ── Chat/Workflow API ────────────────────────────────────────────

    async def run_workflow(
        self,
        inputs: dict,
        user: str = "rdma-agent",
        response_mode: str = "blocking",
    ) -> dict:
        """
        Run a Dify workflow with given inputs.
        The workflow should be configured in Dify's UI with:
        - Input: issue data and diagnostic context
        - Knowledge retrieval node connected to RDMA knowledge base
        - LLM node for analysis
        - Output: structured analysis result
        """
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/workflows/run",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "inputs": inputs,
                    "response_mode": response_mode,
                    "user": user,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def send_chat_message(
        self,
        query: str,
        user: str = "rdma-agent",
        conversation_id: str = "",
        inputs: dict = None,
    ) -> dict:
        """Send a message to a Dify chatbot app."""
        payload = {
            "query": query,
            "user": user,
            "response_mode": "blocking",
            "inputs": inputs or {},
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/chat-messages",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    # ── Knowledge Base / Dataset API ─────────────────────────────────

    async def list_datasets(self) -> list[dict]:
        """List all datasets in Dify."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_base}/datasets",
                headers={"Authorization": f"Bearer {self.dataset_api_key}"},
                params={"page": 1, "limit": 100},
            )
            resp.raise_for_status()
            return resp.json().get("data", [])

    async def create_dataset(self, name: str, description: str = "") -> dict:
        """Create a new dataset for RDMA knowledge."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.api_base}/datasets",
                headers={"Authorization": f"Bearer {self.dataset_api_key}"},
                json={
                    "name": name,
                    "description": description or f"RDMA knowledge base: {name}",
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def upload_document(
        self, dataset_id: str, file_path: str
    ) -> dict:
        """Upload a document to a Dify dataset."""
        async with httpx.AsyncClient(timeout=120) as client:
            with open(file_path, "rb") as f:
                resp = await client.post(
                    f"{self.api_base}/datasets/{dataset_id}/document/create-by-file",
                    headers={"Authorization": f"Bearer {self.dataset_api_key}"},
                    files={"file": f},
                    data={
                        "indexing_technique": "high_quality",
                        "process_rule": json.dumps({"mode": "automatic"}),
                    },
                )
                resp.raise_for_status()
                return resp.json()

    async def create_document_by_text(
        self, dataset_id: str, name: str, text: str
    ) -> dict:
        """Create a document from text in a Dify dataset."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.api_base}/datasets/{dataset_id}/document/create-by-text",
                headers={"Authorization": f"Bearer {self.dataset_api_key}"},
                json={
                    "name": name,
                    "text": text,
                    "indexing_technique": "high_quality",
                    "process_rule": {"mode": "automatic"},
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def query_dataset(
        self, dataset_id: str, query: str, top_k: int = 5
    ) -> list[dict]:
        """Query a dataset for relevant documents."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.api_base}/datasets/{dataset_id}/retrieve",
                headers={"Authorization": f"Bearer {self.dataset_api_key}"},
                json={
                    "query": query,
                    "retrieve_strategy": "semantic_search",
                    "top_k": top_k,
                },
            )
            resp.raise_for_status()
            return resp.json().get("records", [])


# ── Dify Workflow DSL Templates ──────────────────────────────────────

DIFY_WORKFLOW_TEMPLATE = {
    "description": "RDMA Issue Analysis Workflow - Import this into Dify.ai",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "title": "Issue Input",
            "variables": [
                {"name": "issue_summary", "type": "string", "required": True},
                {"name": "severity", "type": "string", "required": True},
                {"name": "category", "type": "string", "required": True},
                {"name": "diagnostic_data", "type": "string", "required": True},
            ],
        },
        {
            "id": "knowledge_retrieval",
            "type": "knowledge-retrieval",
            "title": "Query RDMA Knowledge Base",
            "dataset_ids": ["<RDMA_DATASET_ID>"],
            "query": "{{issue_summary}} {{category}}",
            "retrieval_mode": "semantic_search",
            "top_k": 5,
            "reranking_model": {
                "provider": "openai_api_compatible",
                "model": "<RERANK_MODEL_NAME>",
            },
        },
        {
            "id": "llm_analysis",
            "type": "llm",
            "title": "LLM Root Cause Analysis",
            "model": {
                "provider": "openai_api_compatible",
                "name": "<LLM_MODEL_NAME>",
            },
            "prompt_template": {
                "system": "You are an expert RDMA network troubleshooting agent...",
                "user": (
                    "Issue: {{issue_summary}}\n"
                    "Severity: {{severity}}\n"
                    "Category: {{category}}\n"
                    "Diagnostic Data: {{diagnostic_data}}\n"
                    "Knowledge Context: {{#knowledge_retrieval.result#}}\n\n"
                    "Analyze this issue and provide a JSON action plan."
                ),
            },
        },
        {
            "id": "output",
            "type": "end",
            "title": "Analysis Result",
            "outputs": [
                {"name": "analysis", "value": "{{#llm_analysis.text#}}"},
            ],
        },
    ],
    "edges": [
        {"source": "start", "target": "knowledge_retrieval"},
        {"source": "knowledge_retrieval", "target": "llm_analysis"},
        {"source": "llm_analysis", "target": "output"},
    ],
}
