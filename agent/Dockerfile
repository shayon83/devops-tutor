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
# The python:3.11-slim base ships a setuptools whose vendored copies of
# jaraco.context and wheel carry HIGH CVEs that have fixes available
# (CVE-2026-23949, CVE-2026-24049). Nothing here imports them at runtime, but
# "unused at runtime" is not a reason to ship a known hole, and the Trivy gate
# in CI flags any fixable HIGH. setuptools 84.0.0 vendors jaraco_context 6.1.0
# and wheel 0.46.3, both above the fixed versions.
RUN pip install --no-cache-dir --upgrade "setuptools==84.0.0" \
    && pip install --no-cache-dir -r ./agent/requirements.txt

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
