# Spec Delta

## MODIFIED Requirements

### Requirement: Socratic DevOps Voice Interaction and Dual-Pipeline Support
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with Direct Speech-to-Speech LLM inference (~350ms response latency), while supporting configurable `.env` feature flags (`VOICE_PIPELINE_MODE=realtime|modular`) to switch between realtime audio streaming and modular cascaded VAD + STT + LLM + TTS processing.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Pipeline mode toggle via environment variable
- **WHEN** `VOICE_PIPELINE_MODE` is set to `modular` in `.env`
- **THEN** the agent worker instantiates the modular VAD (Silero) + Deepgram STT + LLM (GPT-4o-mini/Gemini) + ElevenLabs/OpenAI TTS pipeline without altering the WebRTC or Redis interface.

#### Scenario: LiveKit Managed Inference mode toggle
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `cloud` in `.env`
- **THEN** the agent worker connects and routes audio and AI tokens through LiveKit Cloud managed infrastructure.

## ADDED Requirements

### Requirement: Agent Worker Dispatch and Deployment Target Control
The system SHALL support an explicit environment configuration (`AGENT_DISPATCH_TYPE=local|cloud`) to govern agent worker lifecycle and room job dispatch independently of the voice pipeline processing mode.

#### Scenario: Self-hosted local container worker dispatch
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `local` in `.env`
- **THEN** the agent worker initializes within the local container environment (Docker Compose) and registers directly with the LiveKit SFU instance to listen for incoming room job requests.

#### Scenario: LiveKit Cloud managed serverless dispatch
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `cloud` in `.env`
- **THEN** room connection requests automatically route job dispatching to LiveKit Cloud Agents serverless infrastructure.
