# syntax=docker/dockerfile:1
FROM python:3.11-slim

# PYTHONUNBUFFERED keeps logs flowing to the Docker json log (and so to
# Promtail -> Loki) instead of sitting in a buffer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# No build-essential/git: every runtime dependency ships a manylinux wheel.
COPY agent/requirements.txt ./agent/requirements.txt
RUN pip install --no-cache-dir -r ./agent/requirements.txt

COPY shared/ ./shared/
COPY agent/ ./agent/

# LiveKit Agents runs each job in its own process, so prometheus_client needs a
# shared multiprocess directory that the worker and every job can write to.
RUN useradd --create-home --uid 10001 agent \
    && mkdir -p /tmp/prometheus-multiproc \
    && chown -R agent:agent /app /tmp/prometheus-multiproc
USER 10001

EXPOSE 8001

CMD ["python", "-m", "agent.src.agent", "start"]
