# Spec Delta

## MODIFIED Requirements

### Requirement: Socratic DevOps Voice Interaction and Dual-Pipeline Support
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with LiveKit Cloud Managed Inference (`from livekit.agents import inference`) without requiring local third-party API keys or local worker dispatch configurations.

#### Scenario: Real-time voice interaction with LiveKit Cloud Managed Inference
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the LiveKit Cloud serverless agent worker receives the audio stream, processes inference through LiveKit Cloud Managed Inference, and responds concisely (< 3 sentences) in a warm, Socratic SRE voice.

#### Scenario: Zero 3rd-party API key execution
- **WHEN** the LiveKit Agent worker initializes
- **THEN** model inference (STT, LLM, TTS) routes directly through LiveKit Cloud credits without checking or requiring local OpenAI, Deepgram, or ElevenLabs keys.
