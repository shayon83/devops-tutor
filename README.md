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

## 🎛️ Pipeline Modes & Deployment Settings Guide

The application separates voice architecture and inference deployment into **2 orthogonal settings** in `.env`:

1. **`AGENT_DISPATCH_TYPE`** (`cloud` | `local`): Controls model inference & worker deployment.
   - `cloud`: **LiveKit Cloud Managed Inference Gateway**. Zero 3rd-party API keys required! STT, LLM, and TTS models route directly through LiveKit Cloud credits (`from livekit.agents import inference`).
   - `local`: **Self-Hosted Worker (BYOK - Bring Your Own Key)**. Self-hosted Python worker requiring your own API keys (`OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`).

2. **`VOICE_PIPELINE_MODE`** (`realtime` | `modular`): Controls the AI model architecture.
   - `realtime`: Direct Speech-to-Speech audio tokens (~350ms latency).
   - `modular`: Cascaded STT (Deepgram/Whisper) $\rightarrow$ LLM (GPT-4o-mini/Gemma) $\rightarrow$ TTS (ElevenLabs/OpenAI) pipeline.

```text
+---------------------------------------------------------------------------------------+
|                              2D CONFIGURATION MATRIX                                  |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  [ Cloud + Realtime ]  (AGENT_DISPATCH_TYPE=cloud, VOICE_PIPELINE_MODE=realtime)      |
|  - LiveKit Managed Inference Gateway Direct S2S (Zero extra API keys needed)         |
|                                                                                       |
|  [ Cloud + Modular ]   (AGENT_DISPATCH_TYPE=cloud, VOICE_PIPELINE_MODE=modular)       |
|  - LiveKit Managed Inference Gateway STT/LLM/TTS (Zero extra API keys needed)         |
|                                                                                       |
|  [ Local + Realtime ]  (AGENT_DISPATCH_TYPE=local, VOICE_PIPELINE_MODE=realtime)      |
|  - Self-hosted Docker BYOK worker using OpenAI / Azure OpenAI Realtime S2S           |
|                                                                                       |
|  [ Local + Modular ]   (AGENT_DISPATCH_TYPE=local, VOICE_PIPELINE_MODE=modular)       |
|  - Self-hosted Docker BYOK worker using Deepgram + ElevenLabs + OpenAI LLM            |
+---------------------------------------------------------------------------------------+
```

### Quick `.env` Setup Examples:

#### Example 1: LiveKit Cloud Managed Inference (No 3rd-party keys needed!)
```bash
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
AGENT_DISPATCH_TYPE=cloud
VOICE_PIPELINE_MODE=realtime
```

#### Example 2: Local Docker Worker with BYOK (OpenAI API Key)
```bash
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
AGENT_DISPATCH_TYPE=local
VOICE_PIPELINE_MODE=realtime
OPENAI_API_KEY=sk-proj-your-openai-key
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
