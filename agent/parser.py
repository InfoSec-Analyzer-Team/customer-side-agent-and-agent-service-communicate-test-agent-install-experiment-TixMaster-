from __future__ import annotations

import re
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Matches both nginx combined and apache combined format:
# $remote_addr - $remote_user [$time_local] "$method $url $proto" $status $bytes "$referer" "$user_agent"
_COMBINED_RE = re.compile(
    r'^(\S+)'                    # remote_addr
    r' \S+ \S+'                  # ident, auth (both usually "-")
    r' \[([^\]]+)\]'             # [time_local]
    r' "(\S+) (\S+) [^"]*"'      # "METHOD URL PROTO"
    r' (\d{3})'                  # status
    r' (\d+|-)'                  # bytes sent ("-" = 0)
    r'(?: "([^"]*)")?'           # optional referer
    r'(?: "([^"]*)")?'           # optional user_agent
)

_TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


def _parse_time(s: str) -> str:
    try:
        return datetime.strptime(s, _TIME_FMT).isoformat()
    except ValueError:
        return s  # return raw string if unparseable


def _parse_combined(line: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    m = _COMBINED_RE.match(line)
    if not m:
        logger.error("parse_combined failed: %r", line[:200])
        return None

    remote_addr, time_local, method, url, status, size, referer, user_agent = m.groups()

    return {
        "tenant_id": tenant_id,
        "timestamp": _parse_time(time_local),
        "source_ip": remote_addr,
        "event_type": "web_access",
        "user_agent": user_agent or "",
        "payload": {
            "method": method,
            "url": url,
            "status": int(status),
            "size": 0 if size == "-" else int(size),
            "referer": referer or "",
        },
        "raw_payload": line,
    }


def parse_line(line: str, fmt: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    line = line.rstrip("\n")
    if not line:
        return None
    if fmt in ("nginx_combined", "apache_combined"):
        return _parse_combined(line, tenant_id)
    logger.error("unknown log format: %s", fmt)
    return None
