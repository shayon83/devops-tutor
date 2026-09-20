# DevOps Voice Tutor Web Application

An enterprise-grade, real-time interactive **DevOps Voice Tutor** web application built with **LiveKit WebRTC**, **Direct Speech-to-Speech LLM Inference** (OpenAI/Gemini Realtime API), **Redis 7** state persistence, and a full **Grafana Observability Stack** (Prometheus + Loki + Grafana).

---

## 🏗️ Architecture Overview

The system follows a clean, decoupled 5-tier architecture:

```text
+---------------------------------------------------------------------------------------+
|                                  SYSTEM ARCHITECTURE                                  |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  +--------------------+         WebRTC Audio Track            +--------------------+  |
|  |  React/Vite Web    | <===================================> |   LiveKit Cloud    |  |
|  |     Frontend       |                                       |   / Server SFU     |  |
|  +--------------------+                                       +--------------------+  |
|         | REST / Token API                                              ^             |
|         v                                                               | WebRTC / Data
|  +--------------------+                                                 v             |
|  |  FastAPI Backend   |                                       +--------------------+  |
|  | Token & Session API|                                       | LiveKit Agent      |  |
|  +--------------------+                                       | Worker (Python)    |  |
|         |                                                     +--------------------+  |
|         v                                                               |             |
|  +--------------------+       Async State & History Sync                |             |
|  |  Redis 7 Store     | <===============================================+             |
|  | Sessions/History   |                                                               |
|  +--------------------+                                                               |
|         ^                                                                             |
|         | Scrape metrics & logs                                                       |
|  +--------------------+       +--------------------+       +--------------------+     |
|  | Prometheus Metrics | ----> | Loki Log Engine    | ----> | Grafana Dashboard  |     |
|  | (Port 9090)        |       | (Port 3100)        |       | (Port 3001)        |     |
|  +--------------------+       +--------------------+       +--------------------+     |
+---------------------------------------------------------------------------------------+
```

---

## 🎛️ LiveKit Cloud Managed Inference Architecture

The application uses **LiveKit Cloud Managed Inference** (`from livekit.agents import inference`) for speech recognition, LLM reasoning, and voice synthesis:

- **Zero 3rd-Party API Keys**: All AI model calls (STT, LLM, TTS) route natively through LiveKit Cloud credits without requiring third-party provider API keys (`OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, etc.).
- **Serverless Cloud Dispatch**: The agent worker connects directly to LiveKit Cloud SFU (`wss://voice-16bkzz25.livekit.cloud`) and dispatches dynamically for active student WebRTC rooms.

### Quick `.env` Setup:

```bash
# 1. LiveKit Cloud Credentials (Required)
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# 2. Infrastructure Ports
REDIS_HOST=redis
REDIS_PORT=6379
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

2. **Redis 7 as Backing State Store**:
   - **Decision**: Decoupled session state, conversation turn history (`RPUSH`), takeaways, and CSAT feedback under `session:<id>:*` keys.
   - **Rationale**: Sub-millisecond reads/writes prevent state sync bottlenecks during live WebRTC voice turns.

3. **LiveKit WebRTC Data Channels (`DataTrack`) for Visual Workspace**:
   - **Decision**: Agent emits structured visual payloads (`[DIAGRAM: ...]`, `[YAML: ...]`) directly over WebRTC Data Channels.
   - **Rationale**: Eliminates the overhead of maintaining secondary WebSocket connections.

---

## 📈 Scalability Awareness: Handling 10,000 Concurrent Sessions

If scaling to 10,000 concurrent tutoring sessions, the following operational changes would be made:

1. **State Tier (Redis Cluster)**:
   - Transition single Redis instance to a **Redis Cluster** with hash-tag sharded keys (`session:{<session_id>}:*`) across master-replica shards.

2. **Agent Worker Tier (Horizontal Pod Autoscaling)**:
   - Deploy Agent Workers as Kubernetes Pods using HPA based on CPU/RAM and active job counts. LiveKit Server's built-in **Job Dispatcher** automatically distributes incoming room job requests (`JobRequest`) across the pool of registered Agent Worker instances.

3. **Stateless API Tier**:
   - Run stateless FastAPI backend instances behind an AWS Application Load Balancer (ALB) or Nginx Ingress controller.

4. **Rate Limiting & Provider Pool**:
   - Implement token bucket rate limiting and multi-provider LLM fallback queues (OpenAI Realtime $\rightarrow$ Gemini Multimodal Live).

---

## 🚀 Quick Start (Docker Compose)

### 1. Prerequisites
- Docker Engine & Docker Compose (`docker compose` or `docker-compose`)

### 2. Configure Environment Variables
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Edit `.env` and fill in your secrets (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`, etc.).

### 3. Build & Run
Launch all application and monitoring containers with a single command:
```bash
docker compose up --build
```

### 4. Access Services
- **Web Application UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend API & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Grafana Monitoring Dashboards**: [http://localhost:3001](http://localhost:3001) *(Login: admin / admin)*
- **Prometheus Metrics Engine**: [http://localhost:9090](http://localhost:9090)
