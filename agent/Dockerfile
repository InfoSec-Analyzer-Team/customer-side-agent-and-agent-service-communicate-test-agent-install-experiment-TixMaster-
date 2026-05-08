FROM python:3.11-slim

# ── non-root user ─────────────────────────────────────────────────────────────
# Running as root inside a container gives an attacker host-level write access
# if the container escapes. A dedicated system user limits blast radius.
RUN groupadd --system xdr-agent && \
    useradd  --system --gid xdr-agent --no-create-home xdr-agent

# ── install Python dependencies ───────────────────────────────────────────────
WORKDIR /opt/xdr-agent

COPY requirements.txt .
# --no-cache-dir keeps the image layer small (~20 MB saved for PyYAML+requests)
RUN pip install --no-cache-dir -r requirements.txt

# ── copy agent source ─────────────────────────────────────────────────────────
COPY agent.py collector.py parser.py buffer.py sender.py config.py ./

# ── runtime directories ───────────────────────────────────────────────────────
# /var/lib/xdr-agent  — SQLite buffer + checkpoint file (must persist across restarts)
# /var/log/xdr-agent  — agent's own log file
# Both should be bind-mounted or named volumes so data survives container replacement.
RUN mkdir -p /var/lib/xdr-agent /var/log/xdr-agent && \
    chown xdr-agent:xdr-agent /var/lib/xdr-agent /var/log/xdr-agent

USER xdr-agent

# Declare mount points so `docker inspect` and compose show them explicitly.
# At runtime the caller must also bind-mount:
#   /etc/xdr-agent/config.yaml   — agent config (read-only)
#   /var/log/nginx (or similar)  — customer web server log directory (read-only)
VOLUME ["/etc/xdr-agent", "/var/lib/xdr-agent", "/var/log/xdr-agent"]

# -u: unbuffered stdout/stderr so `docker logs -f` shows output immediately
# instead of waiting for Python's 8 KB block buffer to fill.
ENTRYPOINT ["python3", "-u", "agent.py"]
CMD ["--config", "/etc/xdr-agent/config.yaml"]
