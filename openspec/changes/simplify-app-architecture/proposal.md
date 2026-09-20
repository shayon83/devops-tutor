# Proposal: Simplify App Architecture with LiveKit Cloud Managed Inference

## Why

With LiveKit Cloud Managed Inference Gateway (`from livekit.agents import inference`), model routing (STT, LLM, TTS) is managed natively by LiveKit Cloud without requiring separate third-party API keys or local self-hosted worker dispatch complexity.

Eliminating Bring-Your-Own-Key (BYOK) fallback paths, local agent worker dispatch logic, and redundant configuration flags (`AGENT_DISPATCH_TYPE`, `VOICE_PIPELINE_MODE`) will dramatically simplify the architecture, remove dead code paths, streamline deployment, and establish a single, robust serverless cloud agent pattern.

## What Changes

- **BREAKING**: Removed `AGENT_DISPATCH_TYPE` and `VOICE_PIPELINE_MODE` configuration environment variables.
- **BREAKING**: Removed Bring-Your-Own-Key (BYOK) fallback code paths for local workers (`livekit.plugins.openai`, `livekit.plugins.deepgram`, `livekit.plugins.elevenlabs`).
- Standardized the agent worker architecture exclusively on **LiveKit Cloud Managed Inference** (`from livekit.agents import inference`) and cloud agent dispatch.
- Refactored `VoicePipelineFactory` into a clean `VoiceAgentFactory` that initializes a single, unified `Agent` using LiveKit Cloud inference models.
- Cleaned up environment templates (`.env.example` and `.env`) to only include required LiveKit SFU credentials, Redis connection options, and service ports.
- Refactored backend and agent codebase to remove dead code, unused helper functions, and unused key validation routines.

## Capabilities

### Modified Capabilities

- `devops-voice-tutor`: Updating agent dispatch and model inference requirements to mandate LiveKit Cloud Managed Inference and cloud agent dispatch, removing BYOK and local worker options.

## Impact

- **`agent/`**: Refactored `agent/src/factory.py` and `agent/src/agent.py` to remove BYOK conditionals and local dispatch logic.
- **`backend/`**: Cleaned up settings and session token endpoints.
- **`.env.example` & `.env`**: Simplified configuration to zero third-party AI keys.
- **`README.md`**: Updated architectural documentation to single-pattern LiveKit Cloud Managed Inference.
