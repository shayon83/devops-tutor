# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
# The python:3.11-slim base ships a setuptools whose vendored copies of
# jaraco.context and wheel carry HIGH CVEs that have fixes available
# (CVE-2026-23949, CVE-2026-24049). Nothing here imports them at runtime, but
# "unused at runtime" is not a reason to ship a known hole, and the Trivy gate
# in CI flags any fixable HIGH. setuptools 84.0.0 vendors jaraco_context 6.1.0
# and wheel 0.46.3, both above the fixed versions.
RUN pip install --no-cache-dir --upgrade "setuptools==84.0.0" \
    && pip install --no-cache-dir -r ./backend/requirements.txt

COPY shared/ ./shared/
COPY backend/ ./backend/

RUN useradd --create-home --uid 10001 backend && chown -R backend:backend /app
USER 10001

EXPOSE 8000

CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
