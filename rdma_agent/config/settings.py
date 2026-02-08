"""
Configuration settings for the RDMA Agent system.
All LLM/Embedding/Rerank models are accessed via OpenAI-compatible API.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """LLM model configuration (OpenAI-compatible API)."""
    api_base: str = os.getenv("LLM_API_BASE", "http://localhost:8080/v1")
    api_key: str = os.getenv("LLM_API_KEY", "not-needed")
    model_name: str = os.getenv("LLM_MODEL_NAME", "llm-model")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))


@dataclass
class EmbeddingConfig:
    """Embedding model configuration (OpenAI-compatible API)."""
    api_base: str = os.getenv("EMBEDDING_API_BASE", "http://localhost:8081/v1")
    api_key: str = os.getenv("EMBEDDING_API_KEY", "not-needed")
    model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "embedding-model")
    dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))


@dataclass
class RerankConfig:
    """Rerank model configuration (OpenAI-compatible API)."""
    api_base: str = os.getenv("RERANK_API_BASE", "http://localhost:8082/v1")
    api_key: str = os.getenv("RERANK_API_KEY", "not-needed")
    model_name: str = os.getenv("RERANK_MODEL_NAME", "rerank-model")
    top_n: int = int(os.getenv("RERANK_TOP_N", "5"))


@dataclass
class DifyConfig:
    """Dify.ai platform configuration."""
    api_base: str = os.getenv("DIFY_API_BASE", "http://localhost:5001/v1")
    api_key: str = os.getenv("DIFY_API_KEY", "")
    dataset_api_key: str = os.getenv("DIFY_DATASET_API_KEY", "")


@dataclass
class MonitorConfig:
    """Monitoring and collection intervals."""
    poll_interval_seconds: int = int(os.getenv("MONITOR_POLL_INTERVAL", "30"))
    log_retention_hours: int = int(os.getenv("LOG_RETENTION_HOURS", "168"))
    alert_cooldown_seconds: int = int(os.getenv("ALERT_COOLDOWN", "300"))
    max_retry_actions: int = int(os.getenv("MAX_RETRY_ACTIONS", "3"))


@dataclass
class AlarmConfig:
    """Alarm / escalation configuration."""
    webhook_url: Optional[str] = os.getenv("ALARM_WEBHOOK_URL")
    email_smtp_host: str = os.getenv("ALARM_SMTP_HOST", "")
    email_smtp_port: int = int(os.getenv("ALARM_SMTP_PORT", "587"))
    email_from: str = os.getenv("ALARM_EMAIL_FROM", "")
    email_to: str = os.getenv("ALARM_EMAIL_TO", "")
    email_password: str = os.getenv("ALARM_EMAIL_PASSWORD", "")


@dataclass
class AppConfig:
    """Top-level application configuration."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    dify: DifyConfig = field(default_factory=DifyConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    alarm: AlarmConfig = field(default_factory=AlarmConfig)
    data_dir: str = os.getenv("RDMA_DATA_DIR", "/var/lib/rdma_agent")
    log_dir: str = os.getenv("RDMA_LOG_DIR", "/var/log/rdma_agent")
    host: str = os.getenv("RDMA_AGENT_HOST", "0.0.0.0")
    port: int = int(os.getenv("RDMA_AGENT_PORT", "8900"))


def load_config() -> AppConfig:
    """Load configuration from environment."""
    return AppConfig()
