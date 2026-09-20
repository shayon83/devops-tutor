# Spec Delta

## MODIFIED Requirements

### Requirement: Socratic DevOps Voice Interaction and Dual-Pipeline Support
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with LiveKit Cloud Managed Inference (`from livekit.agents import inference`) without requiring local third-party API keys or local worker dispatch configurations.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Real-time voice interaction with LiveKit Cloud Managed Inference
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the LiveKit Cloud serverless agent worker receives the audio stream, processes inference through LiveKit Cloud Managed Inference, and responds concisely (< 3 sentences) in a warm, Socratic SRE voice.

#### Scenario: Zero 3rd-party API key execution
- **WHEN** the LiveKit Agent worker initializes
- **THEN** model inference (STT, LLM, TTS) routes directly through LiveKit Cloud credits without checking or requiring local OpenAI, Deepgram, or ElevenLabs keys.

#### Scenario: Pipeline mode toggle via environment variable
- **WHEN** `VOICE_PIPELINE_MODE` is set to `modular` in `.env`
- **THEN** the agent worker instantiates the modular VAD (Silero) + Deepgram STT + LLM (GPT-4o-mini/Gemini) + ElevenLabs/OpenAI TTS pipeline without altering the WebRTC or Redis interface.

#### Scenario: LiveKit Managed Inference mode toggle
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `cloud` in `.env`
- **THEN** the agent worker initializes LiveKit Managed Inference (`from livekit.agents import inference`) routing all STT, LLM, and TTS inference requests directly through LiveKit Cloud credits without requiring 3rd-party API keys.

#### Scenario: Local Worker BYOK mode toggle
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `local` in `.env`
- **THEN** the self-hosted agent worker validates local environment keys (`OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`) and connects directly to provider APIs.
