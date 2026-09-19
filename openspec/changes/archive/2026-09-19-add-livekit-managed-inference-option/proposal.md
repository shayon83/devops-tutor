# Proposal: Add LiveKit Managed Inference Option & Native SFU Prometheus Metrics

## Why

To provide maximum architectural flexibility, the system should explicitly support LiveKit Managed Inference (Cloud Agents) alongside self-hosted Agent workers and direct Native SFU Prometheus metric scraping from LiveKit Cloud (`:7880/metrics`).

## What Changes

- **LiveKit Managed Inference Provider**: Document and support LiveKit Managed Cloud Agents as an optional voice pipeline provider mode (`VOICE_PIPELINE_MODE=livekit_managed`).
- **Native LiveKit SFU Prometheus Metrics**: Add configuration for Prometheus to scrape native LiveKit SFU metrics (`livekit_room_count`, `livekit_audio_packet_loss_ratio`, `livekit_audio_jitter_ms`) directly from LiveKit.
- **Updated Documentation & Architecture Diagrams**: Document Managed Inference tradeoffs and metrics in `README.md` and `workflow.md`.

## Capabilities

### New Capabilities
*(None)*

### Modified Capabilities
- `devops-voice-tutor`: Add requirement for LiveKit Managed Inference and Native SFU Prometheus metric scraping.

## Impact

- **Agent Worker**: `VoicePipelineFactory` extended with `livekit_managed` provider option.
- **Monitoring**: `monitoring/prometheus/prometheus.yml` extended with LiveKit SFU scrape target.
- **Documentation**: `README.md` and `workflow.md` updated.
