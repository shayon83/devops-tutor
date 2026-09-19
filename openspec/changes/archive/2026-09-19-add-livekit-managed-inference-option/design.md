# Technical Design: Add LiveKit Managed Inference Option & Native SFU Metrics

## Context

See `proposal.md` for overall motivation. This design documents the technical architecture for integrating LiveKit Managed Inference (Cloud Agents) as a third pipeline provider mode (`livekit_managed`) and configuring Prometheus scraping for native LiveKit SFU WebRTC metrics.

## Goals / Non-Goals

**Goals:**
- Document LiveKit Managed Inference provider option in `VoicePipelineFactory`.
- Document native LiveKit SFU Prometheus scraping target (`livekit_room_count`, `livekit_audio_packet_loss_ratio`).
- Document visual workspace DataTrack stream parsing latency (~55ms).

**Non-Goals:**
- Removing self-hosted agent worker or Azure OpenAI / OpenAI support.

## Decisions

### 1. Provider Mode Expansion (`livekit_managed`)
- **Decision**: Expand `VOICE_PIPELINE_MODE` in `VoicePipelineFactory` to support `realtime`, `modular`, and `livekit_managed`.
- **Rationale**: Gives users and evaluators complete choice between self-hosted Docker agent workers and LiveKit Cloud managed inference.

### 2. Native LiveKit SFU Prometheus Scraping
- **Decision**: Add Prometheus scrape config target for LiveKit Server SFU.
- **Rationale**: Direct observability of WebRTC audio packet loss, room counts, and jitter metrics in Grafana.
