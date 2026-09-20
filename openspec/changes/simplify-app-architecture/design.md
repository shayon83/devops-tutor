# Technical Design: Simplify App Architecture with LiveKit Cloud Managed Inference

## Context

See `proposal.md` for motivation and background.

Currently, the agent factory (`agent/src/factory.py`) maintains complex fallback branches for `AGENT_DISPATCH_TYPE` (`local` vs `cloud`) and `VOICE_PIPELINE_MODE` (`realtime` vs `modular`), along with validation helper functions (`is_valid_key`) and third-party API key loading (`OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`).

Now that LiveKit Cloud Managed Inference Gateway (`from livekit.agents import inference`) is active, all STT, LLM, and TTS model requests route directly through LiveKit Cloud credits without requiring local worker dispatch or third-party keys.

## Goals / Non-Goals

**Goals:**
- Eliminate `AGENT_DISPATCH_TYPE` and `VOICE_PIPELINE_MODE` environment flags across the codebase.
- Refactor `VoicePipelineFactory` into a clean, single-pattern `VoiceAgentFactory` using `livekit.agents.inference`.
- Remove all BYOK third-party key checks, key validation routines, and local fallback paths.
- Simplify `.env`, `.env.example`, and docker compose configurations.
- Refactor unit test suite in `agent/tests/test_factory.py` to match the simplified single-pattern factory.

**Non-Goals:**
- Modifying FastAPI backend token generation logic (`/api/token`).
- Altering visual workspace rendering over LiveKit `DataTrack` or Redis session persistence.

## Decisions

### Decision 1: Single-Pattern Factory with LiveKit Managed Inference
- **Choice**: Replace conditional `VoicePipelineFactory` with `VoiceAgentFactory`:
  ```python
  from livekit.agents import inference, voice
  from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

  class VoiceAgentFactory:
      @staticmethod
      def create_agent() -> voice.Agent:
          return voice.Agent(
              instructions=DEVOPS_TUTOR_SYSTEM_PROMPT,
              llm=inference.LLM(model="openai/gpt-4o-mini")
          )
  ```
- **Rationale**: Eliminates ~100 lines of complex branching logic, third-party key parsing, and error-prone endpoint validation.

### Decision 2: Streamlined Environment Configuration
- **Choice**: `.env` and `.env.example` only retain:
  - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
  - `REDIS_HOST`, `REDIS_PORT`, `BACKEND_PORT`, `FRONTEND_PORT`
- **Rationale**: Reduces onboarding friction to zero third-party key setup.

### Decision 3: Code Cleanup & Dead Code Removal
- **Choice**: Remove unused `is_valid_key` helper functions, unused imports (`livekit.plugins.openai`, `deepgram`, `elevenlabs`), and unused test mocks.

## Risks / Trade-offs

- **[Risk]**: Running without a valid LiveKit Cloud project token will fail at room connect time.
  - *Mitigation*: The backend `/api/token` endpoint validates LiveKit credentials and returns explicit 500 errors if keys are unconfigured.

## Migration Plan

1. Update `agent/src/factory.py` to simplify `create_agent()`.
2. Update `agent/src/agent.py` to invoke `VoiceAgentFactory.create_agent()`.
3. Clean up `.env.example` and `.env`.
4. Update `agent/tests/test_factory.py` unit tests.
5. Update `README.md` and master specification `spec.md`.
