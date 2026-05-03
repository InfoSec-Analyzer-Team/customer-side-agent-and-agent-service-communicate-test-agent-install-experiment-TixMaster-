#!/usr/bin/env python3
"""XDR Customer Agent — Phase 1 entry point (collector + parser + dry-run)."""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
from threading import Thread

from config import AgentConfig, load_config
from collector import FileCollector
from parser import parse_line

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
        print(f"[warn] cannot open agent log file {cfg.logging.path}: {e}", file=sys.stderr)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        handlers=handlers,
    )


def _run_source(source, cfg: AgentConfig, dry_run: bool, from_beginning: bool) -> None:
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
                print(json.dumps(event, ensure_ascii=False), flush=True)
            # Phase 2: hand off to LocalBuffer here
    finally:
        collector.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=f"XDR Customer Agent v{VERSION}")
    ap.add_argument("--config", default="config.yaml", help="path to config.yaml")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse logs and print events to stdout; do not send to gateway")
    ap.add_argument("--from-beginning", action="store_true",
                    help="ignore checkpoint and read log files from the start (useful for testing)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    _setup_logging(cfg)

    root_log = logging.getLogger("agent")
    root_log.info("XDR Agent v%s  config=%s  dry_run=%s  from_beginning=%s",
                  VERSION, args.config, args.dry_run, args.from_beginning)
    root_log.info("tenant_id=%s  gateway=%s", cfg.tenant_id, cfg.gateway_url)

    if args.dry_run:
        root_log.info("DRY-RUN: events printed to stdout, not sent to gateway")

    for source in cfg.sources:
        root_log.info("source: %s (format=%s)", source.path, source.format)

    threads = [
        Thread(
            target=_run_source,
            args=(source, cfg, args.dry_run, args.from_beginning),
            daemon=True,
            name=f"source-{source.path}",
        )
        for source in cfg.sources
    ]

    for t in threads:
        t.start()

    # Block main thread; exit cleanly on Ctrl-C / SIGTERM
    def _handle_signal(signum, _frame):
        root_log.info("received signal %d, shutting down", signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
