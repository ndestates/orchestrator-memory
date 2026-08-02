# Thin production image for orchestrator license API (DigitalOcean App Platform).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ORCHESTRATOR_LICENSE_SERVER_HOST=0.0.0.0 \
    ORCHESTRATOR_LICENSE_SERVER_PORT=8080 \
    ORCHESTRATOR_LICENSE_DB=/data/licenses.sqlite3

WORKDIR /app

# Minimal tree: only the CLI package (license server is stdlib-only).
COPY src/orchestrator_cli /app/orchestrator_cli
COPY VERSION /app/VERSION

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /data \
    && chown -R app:app /app /data

USER app
EXPOSE 8080

# Health: GET /healthz  Validate: POST /api/licenses/validate
CMD ["python", "-m", "orchestrator_cli.license_server"]
