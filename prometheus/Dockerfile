FROM prom/prometheus:latest
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Railway expects the container to listen on the platform-provided PORT env var.
# Use shell-form CMD so the env var is expanded at container start time.
ENV PORT=9090
CMD prometheus --config.file=/etc/prometheus/prometheus.yml --web.listen-address=:$PORT
