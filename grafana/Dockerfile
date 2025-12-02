FROM grafana/grafana:latest

# Copy provisioning and dashboards from repo into the image so Grafana starts with
# the Prometheus datasource and dashboards already configured.
COPY provisioning /etc/grafana/provisioning
COPY dashboards /var/lib/grafana/dashboards

# Allow anonymous read (optional) - you can change/remove in production
ENV GF_AUTH_ANONYMOUS_ENABLED=true
