#!/usr/bin/env python3
"""XDR Customer Agent — Phase 1 main entry point."""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
from threading import Thread
from typing import Optional

from buffer import LocalBuffer
from collector import FileCollector
from config import AgentConfig, load_config
from parser import parse_line
from sender import BatchSender

VERSION = "0.1.0"


def _setup_logging(cfg: AgentConfig) -> None:
    log_dir = os.path.dirname(cfg.logging.path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, cfg.logging.level.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        handlers.append(logging.FileHandler(cfg.logging.path))
    except OSError as e:
        print(f"[warn] cannot open log file {cfg.logging.path}: {e}", file=sys.stderr)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        handlers=handlers,
    )


def _run_source(
    source,
    cfg: AgentConfig,
    dry_run: bool,
    from_beginning: bool,
    buffer: Optional[LocalBuffer],
) -> None:
    """Collect + parse one log source; hand events to buffer (or stdout in dry-run)."""
    logger = logging.getLogger(f"source[{source.path}]")
    logger.info("starting (format=%s from_beginning=%s)", source.format, from_beginning)

    cp_dir = os.path.dirname(cfg.checkpoint.path)
    if cp_dir:
        os.makedirs(cp_dir, exist_ok=True)

    collector = FileCollector(
        path=source.path,
        checkpoint_path=cfg.checkpoint.path,
        from_beginning=from_beginning,
    )

    try:
        for line in collector.tail():
            event = parse_line(line, source.format, cfg.tenant_id)
            if event is None:
                continue

            if dry_run:
                # In dry-run mode we skip the buffer entirely and print directly
                # so the user can inspect parsed events without touching disk.
                print(json.dumps(event, ensure_ascii=False), flush=True)
            else:
                # Push one event at a time; SQLite WAL keeps this cheap.
                # The sender thread reads in chunk_size batches independently.
                buffer.push([event])
    finally:
        collector.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=f"XDR Customer Agent v{VERSION}")
    ap.add_argument("--config", default="config.yaml", help="path to config.yaml")
    ap.add_argument(
        "--dry-run", action="store_true",
        help="parse logs and print JSON to stdout; skip buffer and gateway",
    )
    ap.add_argument(
        "--from-beginning", action="store_true",
        help="ignore checkpoint; read log files from offset 0 (useful for testing)",
    )
    args = ap.parse_args()

    cfg = load_config(args.config)
    _setup_logging(cfg)

    root_log = logging.getLogger("agent")
    root_log.info(
        "XDR Agent v%s  config=%s  dry_run=%s  from_beginning=%s",
        VERSION, args.config, args.dry_run, args.from_beginning,
    )
    root_log.info("tenant_id=%s  gateway=%s", cfg.tenant_id, cfg.gateway_url)

    for source in cfg.sources:
        root_log.info("source: %s (format=%s)", source.path, source.format)

    # ── buffer + sender (skipped in dry-run) ──────────────────────────────────
    buffer: Optional[LocalBuffer] = None
    sender: Optional[BatchSender] = None
    sender_thread: Optional[Thread] = None

    if not args.dry_run:
        buffer = LocalBuffer(cfg.buffer.path, cfg.buffer.max_size_mb)
        sender = BatchSender(cfg, buffer)
        sender_thread = Thread(target=sender.run, daemon=True, name="sender")
        sender_thread.start()
        root_log.info(
            "buffer: %s  flush_interval=%ds  chunk=%d",
            cfg.buffer.path, cfg.batch.flush_interval_sec, cfg.batch.chunk_size,
        )
    else:
        root_log.info("DRY-RUN: buffer and sender disabled; events go to stdout")

    # ── one thread per log source ─────────────────────────────────────────────
    source_threads = [
        Thread(
            target=_run_source,
            args=(source, cfg, args.dry_run, args.from_beginning, buffer),
            daemon=True,
            name=f"source-{source.path}",
        )
        for source in cfg.sources
    ]
    for t in source_threads:
        t.start()

    # ── graceful shutdown on Ctrl-C / SIGTERM ─────────────────────────────────
    def _handle_signal(signum, _frame):
        root_log.info("signal %d received — shutting down", signum)
        if sender:
            # stop() sets an event that causes run() to do a final flush
            # before the thread exits, so we don't lose buffered events.
            sender.stop()
            sender_thread.join(timeout=90)  # wait up to 90s for final flush
        if buffer:
            buffer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    for t in source_threads:
        t.join()


if __name__ == "__main__":
    main()
