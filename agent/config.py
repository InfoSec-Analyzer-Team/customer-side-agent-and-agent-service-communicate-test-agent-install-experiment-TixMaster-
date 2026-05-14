from __future__ import annotations

import os
import sys
import tempfile
import yaml
from dataclasses import dataclass, field
from typing import List


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
class AgentConfig:
    tenant_id: str
    gateway_url: str
    sources: List[SourceConfig]
    batch: BatchConfig = field(default_factory=BatchConfig)
    buffer: BufferConfig = field(default_factory=BufferConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config(path: str) -> AgentConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    sources = [SourceConfig(**s) for s in raw["sources"]]

    return AgentConfig(
        tenant_id=raw["tenant_id"],
        gateway_url=raw["gateway_url"],
        sources=sources,
        batch=BatchConfig(**raw.get("batch", {})),
        buffer=BufferConfig(**raw.get("buffer", {})),
        retry=RetryConfig(**raw.get("retry", {})),
        checkpoint=CheckpointConfig(**raw.get("checkpoint", {})),
        logging=LoggingConfig(**raw.get("logging", {})),
    )
