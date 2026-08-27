from __future__ import annotations

import os
import sys
import tempfile
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


def _resolve_path(path: str) -> str:
    """On Windows, remap Linux absolute paths under %TEMP%/xdr-agent/."""
    if sys.platform != "win32" or not path.startswith("/"):
        return path
    relative = path.lstrip("/")
    return os.path.join(tempfile.gettempdir(), "xdr-agent", relative)


@dataclass
class SourceConfig:
    type: str
    path: str
    format: str

    def __post_init__(self) -> None:
        self.path = _resolve_path(self.path)


@dataclass
class BatchConfig:
    flush_interval_sec: int = 180
    chunk_size: int = 5000


@dataclass
class BufferConfig:
    path: str = "/var/lib/xdr-agent/buffer.db"
    max_size_mb: int = 200

    def __post_init__(self) -> None:
        self.path = _resolve_path(self.path)


@dataclass
class RetryConfig:
    max_attempts: int = 10
    base_delay_sec: float = 1.0
    max_delay_sec: float = 60.0


@dataclass
class CheckpointConfig:
    path: str = "/var/lib/xdr-agent/checkpoint.json"

    def __post_init__(self) -> None:
        self.path = _resolve_path(self.path)


@dataclass
class LoggingConfig:
    level: str = "INFO"
    path: str = "/var/log/xdr-agent/agent.log"

    def __post_init__(self) -> None:
        self.path = _resolve_path(self.path)


@dataclass
class HeartbeatConfig:
    interval_sec: int = 30


@dataclass
class AgentConfig:
    tenant_id: str
    gateway_url: str
    sources: List[SourceConfig]
    # Ingest API Key（平台 Portal 產生）：所有請求以 Authorization: Bearer <api_key> 帶出。
    # 憑證優先從環境變數 XDR_API_KEY 讀取（見 xdr-agent.service 的 EnvironmentFile），
    # 其次才是 config.yaml，避免明碼憑證落進版控。留空＝匿名（相容 Gateway 過渡期）。
    api_key: Optional[str] = None
    # 本 Agent 在平台的識別碼（Portal 產生）。權威身分仍以 api_key 對應為準，此欄僅供
    # 顯示與心跳歸屬，會放在批次信封層 / 心跳事件送出。
    agent_id: Optional[str] = None
    batch: BatchConfig = field(default_factory=BatchConfig)
    buffer: BufferConfig = field(default_factory=BufferConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)


def load_config(path: str) -> AgentConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    sources = [SourceConfig(**s) for s in raw["sources"]]

    # 憑證：環境變數 XDR_API_KEY 優先於 config.yaml（敏感值不落版控）。
    api_key = os.getenv("XDR_API_KEY") or raw.get("api_key") or None

    return AgentConfig(
        tenant_id=raw["tenant_id"],
        gateway_url=raw["gateway_url"],
        sources=sources,
        api_key=api_key,
        agent_id=raw.get("agent_id") or None,
        batch=BatchConfig(**raw.get("batch", {})),
        buffer=BufferConfig(**raw.get("buffer", {})),
        retry=RetryConfig(**raw.get("retry", {})),
        checkpoint=CheckpointConfig(**raw.get("checkpoint", {})),
        logging=LoggingConfig(**raw.get("logging", {})),
        heartbeat=HeartbeatConfig(**raw.get("heartbeat", {})),
    )
