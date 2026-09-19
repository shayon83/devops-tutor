# Proposal

## Why

Currently, the master specification (`openspec/specs/devops-voice-tutor/spec.md`) conflates the voice pipeline architecture (`VOICE_PIPELINE_MODE=realtime|modular`) with deployment execution dispatch (`AGENT_DISPATCH_TYPE=local|cloud`) by embedding `livekit_managed` as an option under `VOICE_PIPELINE_MODE`. Audio processing strategy and worker deployment target are two independent, orthogonal architectural dimensions. Formally updating the spec to reflect the 2×2 settings matrix ensures accurate governance, zero ambiguity for developers/evaluators, and clean alignment across `.env.example`, code, and documentation.

## What Changes

- Update `Requirement: Socratic DevOps Voice Interaction and Dual-Pipeline Support` to define `VOICE_PIPELINE_MODE` (`realtime` | `modular`) strictly for speech processing architecture.
- Add an explicit requirement / scenarios for `AGENT_DISPATCH_TYPE` (`local` | `cloud`) to govern worker dispatch and deployment targets.
- Clarify that all 4 matrix quadrants (including **Cloud + Modular**) are valid operational configurations.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `devops-voice-tutor`: Updating voice pipeline requirements and introducing explicit agent dispatch type requirement scenarios to reflect the 2D orthogonal matrix.

## Impact

- `openspec/specs/devops-voice-tutor/spec.md` (Master specification sync target)
- Documentation and environment variable guidelines in `README.md` and `.env.example`
