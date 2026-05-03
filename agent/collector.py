from __future__ import annotations

import json
import logging
import os
import time
from typing import IO, Iterator, Optional

logger = logging.getLogger(__name__)

_SENTINEL = -1  # offset value meaning "no checkpoint — seek to end"


class FileCollector:
    """Tail a log file and yield new lines, surviving log rotation and restarts."""

    def __init__(
        self,
        path: str,
        checkpoint_path: str,
        poll_interval: float = 0.5,
        from_beginning: bool = False,
    ) -> None:
        self.path = path
        self.checkpoint_path = checkpoint_path
        self.poll_interval = poll_interval
        self.from_beginning = from_beginning

        self._inode: int = 0
        self._offset: int = _SENTINEL
        self._fh: Optional[IO[str]] = None

        self._load_checkpoint()

    # ── checkpoint ──────────────────────────────────────────────────────────

    def _load_checkpoint(self) -> None:
        try:
            with open(self.checkpoint_path) as f:
                data = json.load(f)
            cp = data.get(self.path, {})
            self._inode = cp.get("inode", 0)
            self._offset = cp.get("offset", _SENTINEL)
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # no checkpoint yet; _offset stays _SENTINEL

    def _save_checkpoint(self) -> None:
        try:
            cp_dir = os.path.dirname(self.checkpoint_path)
            if cp_dir:
                os.makedirs(cp_dir, exist_ok=True)

            try:
                with open(self.checkpoint_path) as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}

            data[self.path] = {"inode": self._inode, "offset": self._offset}
            tmp = self.checkpoint_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(tmp, self.checkpoint_path)  # atomic on POSIX
        except OSError as e:
            logger.warning("checkpoint save failed: %s", e)

    # ── file handle ─────────────────────────────────────────────────────────

    def _open(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None
        try:
            fh = open(self.path, "r", errors="replace")
            stat = os.stat(self.path)
            self._inode = stat.st_ino

            if self.from_beginning:
                self._offset = 0
                fh.seek(0)
            elif self._offset == _SENTINEL:
                # First ever open with no checkpoint: tail from end
                fh.seek(0, 2)
                self._offset = fh.tell()
            else:
                fh.seek(self._offset)

            self._fh = fh
            logger.info("opened %s (inode=%d offset=%d)", self.path, self._inode, self._offset)
        except OSError as e:
            logger.warning("cannot open %s: %s", self.path, e)

    def _rotation_detected(self) -> bool:
        try:
            stat = os.stat(self.path)
            if stat.st_ino != self._inode:
                logger.info("rotation detected (inode changed): %s", self.path)
                return True
            if stat.st_size < self._offset:
                logger.info("rotation detected (truncated): %s", self.path)
                return True
        except FileNotFoundError:
            pass
        return False

    # ── public interface ─────────────────────────────────────────────────────

    def tail(self) -> Iterator[str]:
        """Yield lines indefinitely, blocking on poll_interval when no new data."""
        if not self._fh:
            self._open()

        while True:
            if self._rotation_detected():
                self._offset = 0 if not self.from_beginning else 0
                self._open()
                if not self._fh:
                    time.sleep(self.poll_interval)
                    continue

            line = self._fh.readline()
            if line:
                self._offset = self._fh.tell()
                self._save_checkpoint()
                yield line
            else:
                time.sleep(self.poll_interval)

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None
