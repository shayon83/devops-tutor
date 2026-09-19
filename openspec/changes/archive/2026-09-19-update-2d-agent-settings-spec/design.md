# Design

## Context

The system previously referenced `livekit_managed` as a third pipeline option under `VOICE_PIPELINE_MODE`. However, LiveKit Managed Agents describe how/where the agent runs, whereas Speech-to-Speech vs Modular describes how audio frames flow through models. See `proposal.md` for full background.

## Goals / Non-Goals

**Goals:**
- Formalize a clean 2D orthogonal matrix configuration (`VOICE_PIPELINE_MODE` & `AGENT_DISPATCH_TYPE`).
- Ensure `VoicePipelineFactory` and `.env.example` adhere strictly to the 2D matrix model.
- Verify that `VoicePipelineAgent` (modular) and `MultimodalAgent` (realtime) work seamlessly in both local and cloud dispatch settings.

**Non-Goals:**
- Modifying underlying LiveKit agent SDK or changing WebRTC connection protocols.

## Decisions

### Decision 1: Decouple Pipeline Mode from Dispatch Mode
- **Rationale**: Audio model composition (VAD/STT/LLM/TTS vs direct S2S) is completely independent of where the Python worker process is hosted (local Docker container vs LiveKit Cloud).
- **Alternatives Considered**: Combining modes into a single enum like `realtime-local`, `realtime-cloud`, `modular-local`, `modular-cloud`. Rejected due to combinatorial explosion and poor developer ergonomics.

## Risks / Trade-offs

- **[Risk]** Developers using older `.env` files with legacy variable values.
  - **Mitigation**: Update `.env.example` with clear section headers and provide fallback defaults in `agent/src/config.py` / `agent/src/factory.py`.
