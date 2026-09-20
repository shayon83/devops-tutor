FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY agent/requirements.txt ./agent/requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./agent/requirements.txt -r ./backend/requirements.txt

COPY backend/ ./backend/
COPY agent/ ./agent/
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["python", "agent/src/agent.py", "start"]
