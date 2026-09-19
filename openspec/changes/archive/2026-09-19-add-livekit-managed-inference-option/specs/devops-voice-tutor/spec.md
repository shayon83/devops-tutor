# Spec Delta: devops-voice-tutor

## MODIFIED Requirements

### Requirement: Socratic DevOps Voice Interaction and Dual-Pipeline Support
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with Direct Speech-to-Speech LLM inference (~350ms response latency), while supporting configurable `.env` feature flags (`VOICE_PIPELINE_MODE=realtime|modular|livekit_managed`) to switch between realtime, modular, or LiveKit Managed Inference pipelines.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Pipeline mode toggle via environment variable
- **WHEN** `VOICE_PIPELINE_MODE` is set to `modular` in `.env`
- **THEN** the agent worker instantiates the modular VAD + Deepgram STT + LLM + ElevenLabs/OpenAI TTS pipeline without altering the WebRTC or Redis interface.

#### Scenario: LiveKit Managed Inference mode toggle
- **WHEN** `VOICE_PIPELINE_MODE` is set to `livekit_managed` in `.env`
- **THEN** the agent worker initializes LiveKit Managed Inference routing audio and AI tokens through LiveKit Cloud.

### Requirement: Observability Telemetry and Pre-Configured Grafana Dashboards
The system SHALL expose Prometheus metrics for RED signals, End-to-End voice turn latency, barge-in frequency, and talk-time ratios, while scraping native LiveKit SFU metrics (`livekit_room_count`, `livekit_audio_packet_loss_ratio`, `livekit_audio_jitter_ms`), shipping container logs to Loki and provisioning Grafana dashboards automatically on startup.

#### Scenario: Prometheus metric scraping and Grafana dashboard visualization
- **WHEN** voice turns occur during an active session
- **THEN** Prometheus scrapes latency and turn metrics from the application endpoints and Grafana displays real-time latency waterfall and session health dashboards on port 3000.

#### Scenario: Native LiveKit SFU Prometheus metrics scraping
- **WHEN** Prometheus scrapes metrics from the configured targets
- **THEN** Prometheus collects both application turn metrics and native LiveKit SFU audio quality metrics for Grafana visualization.
