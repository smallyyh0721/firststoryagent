"""
Knowledge Manager - RAG pipeline for RDMA expertise.
Uses Dify.ai dataset API or direct embedding + vector store for retrieval.
Supports both Dify-managed and local ChromaDB knowledge bases.
"""

import logging
import json
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    Manages the RAG knowledge base for RDMA troubleshooting.

    Two modes:
    1. Dify Dataset API mode - uses Dify's built-in knowledge base
    2. Local mode - uses local embedding model + ChromaDB
    """

    def __init__(
        self,
        mode: str = "dify",
        dify_api_base: str = "http://localhost:5001/v1",
        dify_dataset_api_key: str = "",
        embedding_api_base: str = "http://localhost:8081/v1",
        embedding_api_key: str = "not-needed",
        embedding_model: str = "embedding-model",
        rerank_api_base: str = "http://localhost:8082/v1",
        rerank_api_key: str = "not-needed",
        rerank_model: str = "rerank-model",
        rerank_top_n: int = 5,
        chroma_persist_dir: str = "/var/lib/rdma_agent/chroma",
    ):
        self.mode = mode
        self.dify_api_base = dify_api_base.rstrip("/")
        self.dify_dataset_api_key = dify_dataset_api_key
        self.embedding_api_base = embedding_api_base.rstrip("/")
        self.embedding_api_key = embedding_api_key
        self.embedding_model = embedding_model
        self.rerank_api_base = rerank_api_base.rstrip("/")
        self.rerank_api_key = rerank_api_key
        self.rerank_model = rerank_model
        self.rerank_top_n = rerank_top_n
        self.chroma_persist_dir = chroma_persist_dir
        self._chroma_client = None
        self._collection = None

    # ── Dify Dataset API Mode ────────────────────────────────────────

    async def query_dify_knowledge(self, query: str, dataset_id: str, top_k: int = 5) -> list[dict]:
        """Query Dify knowledge base via Dataset API."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.dify_api_base}/datasets/{dataset_id}/retrieve",
                headers={"Authorization": f"Bearer {self.dify_dataset_api_key}"},
                json={
                    "query": query,
                    "retrieve_strategy": "semantic_search",
                    "top_k": top_k,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("records", [])

    async def create_dify_dataset(self, name: str) -> str:
        """Create a new Dify dataset and return its ID."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.dify_api_base}/datasets",
                headers={"Authorization": f"Bearer {self.dify_dataset_api_key}"},
                json={"name": name},
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def upload_document_to_dify(
        self, dataset_id: str, file_path: str, doc_type: str = "text"
    ) -> dict:
        """Upload a document to a Dify dataset."""
        async with httpx.AsyncClient(timeout=120) as client:
            with open(file_path, "rb") as f:
                resp = await client.post(
                    f"{self.dify_api_base}/datasets/{dataset_id}/document/create-by-file",
                    headers={"Authorization": f"Bearer {self.dify_dataset_api_key}"},
                    files={"file": f},
                    data={
                        "indexing_technique": "high_quality",
                        "process_rule": json.dumps({
                            "mode": "automatic",
                        }),
                    },
                )
                resp.raise_for_status()
                return resp.json()

    # ── Local ChromaDB Mode ──────────────────────────────────────────

    def _init_chroma(self):
        """Initialize ChromaDB client lazily."""
        if self._chroma_client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                os.makedirs(self.chroma_persist_dir, exist_ok=True)
                self._chroma_client = chromadb.PersistentClient(
                    path=self.chroma_persist_dir
                )
                self._collection = self._chroma_client.get_or_create_collection(
                    name="rdma_knowledge",
                    metadata={"hnsw:space": "cosine"},
                )
            except ImportError:
                raise RuntimeError("chromadb not installed. Run: pip install chromadb")

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding from the local embedding model via OpenAI-compatible API."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.embedding_api_base}/embeddings",
                headers={"Authorization": f"Bearer {self.embedding_api_key}"},
                json={"input": text, "model": self.embedding_model},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]

    async def _rerank(self, query: str, documents: list[str]) -> list[dict]:
        """Rerank documents using the rerank model via OpenAI-compatible API."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.rerank_api_base}/rerank",
                headers={"Authorization": f"Bearer {self.rerank_api_key}"},
                json={
                    "model": self.rerank_model,
                    "query": query,
                    "documents": documents,
                    "top_n": self.rerank_top_n,
                },
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    async def add_document_local(self, doc_id: str, text: str, metadata: dict = None):
        """Add a document to the local ChromaDB knowledge base."""
        self._init_chroma()
        embedding = await self._get_embedding(text)
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
        )

    async def query_local(self, query: str, top_k: int = 10) -> list[dict]:
        """Query local ChromaDB, then rerank results."""
        self._init_chroma()
        query_embedding = await self._get_embedding(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        ids = results["ids"][0]
        metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)

        # Rerank
        try:
            reranked = await self._rerank(query, docs)
            ranked_results = []
            for item in reranked:
                idx = item["index"]
                ranked_results.append({
                    "id": ids[idx],
                    "text": docs[idx],
                    "metadata": metadatas[idx],
                    "score": item.get("relevance_score", 0),
                })
            return ranked_results
        except Exception as e:
            logger.warning("Rerank failed, returning raw results: %s", e)
            return [
                {"id": ids[i], "text": docs[i], "metadata": metadatas[i], "score": 0}
                for i in range(len(docs))
            ]

    # ── Unified Query Interface ──────────────────────────────────────

    async def query(self, query: str, dataset_id: str = "", top_k: int = 5) -> list[dict]:
        """
        Query knowledge base using configured mode.
        Returns list of {"text": ..., "score": ..., "metadata": ...}
        """
        if self.mode == "dify" and dataset_id:
            records = await self.query_dify_knowledge(query, dataset_id, top_k)
            return [
                {
                    "text": r.get("segment", {}).get("content", ""),
                    "score": r.get("score", 0),
                    "metadata": r.get("segment", {}).get("keywords", []),
                }
                for r in records
            ]
        else:
            return await self.query_local(query, top_k)
