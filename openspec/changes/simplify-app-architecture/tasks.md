# Tasks

## 1. Agent Factory Refactoring

- [ ] 1.1 Refactor `agent/src/factory.py` to create `VoiceAgentFactory` using LiveKit Cloud Managed Inference (`from livekit.agents import inference`) and remove all BYOK key validation routines (`is_valid_key`) and `VOICE_PIPELINE_MODE` / `AGENT_DISPATCH_TYPE` conditionals. Verify with `PYTHONPATH=. .venv/bin/pytest agent/tests/`.
- [ ] 1.2 Update `agent/src/agent.py` to instantiate `VoiceAgentFactory.create_agent()` directly. Verify syntax with `.venv/bin/python -m py_compile agent/src/agent.py`.

## 2. Environment & Configuration Simplification

- [ ] 2.1 Update `.env.example` to remove third-party AI keys (`OPENAI_API_KEY`, `AZURE_OPENAI_...`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`) and dispatch flags (`AGENT_DISPATCH_TYPE`, `VOICE_PIPELINE_MODE`). Verify file syntax.
- [ ] 2.2 Update `.env` to remove unused configuration flags and third-party key placeholders. Verify container restart with `docker compose restart agent`.

## 3. Test Suite & Documentation Updates

- [ ] 3.1 Refactor `agent/tests/test_factory.py` to test `VoiceAgentFactory.create_agent()` without key environment variable mocks. Verify with `PYTHONPATH=. .venv/bin/pytest agent/tests/`.
- [ ] 3.2 Update `README.md` to document the simplified single-pattern LiveKit Cloud Managed Inference architecture. Verify markdown formatting.
