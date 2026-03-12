FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps — install in two steps so Docker caches the layer
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && \
    playwright install chromium && \
    playwright install-deps chromium

# App code
COPY alembic.ini ./
COPY alembic/ alembic/
COPY app/ app/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
