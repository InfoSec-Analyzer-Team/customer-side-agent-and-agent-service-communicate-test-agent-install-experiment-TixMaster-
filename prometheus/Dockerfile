FROM prom/prometheus:latest
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY prometheus_rules.yml /etc/prometheus/prometheus_rules.yml

# Railway expects the container to listen on the platform-provided PORT env var.
# The official Prometheus image sets an ENTRYPOINT to the prometheus binary.
# If we provide a shell-form CMD while the image has an ENTRYPOINT, Docker will
# pass the shell (/bin/sh) as an argument to the prometheus binary which causes
# "unexpected /bin/sh" errors. To allow environment variable expansion for
# $PORT we clear the ENTRYPOINT and run a shell explicitly.

ENV PORT=9090

# Clear any ENTRYPOINT from the base image so we don't accidentally pass
# /bin/sh as an argument to the prometheus binary.
ENTRYPOINT []

# Run Prometheus through a small shell command so $PORT is expanded at runtime.
CMD ["sh", "-c", "exec prometheus --config.file=/etc/prometheus/prometheus.yml --web.listen-address=:$PORT"]
