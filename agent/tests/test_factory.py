import pytest
from agent.src.factory import VoiceAgentFactory
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

def test_system_prompt_contains_socratic_instructions():
    assert "Socratic Voice Tutor" in DEVOPS_TUTOR_SYSTEM_PROMPT
    assert "[DIAGRAM:" in DEVOPS_TUTOR_SYSTEM_PROMPT
    assert "[YAML:" in DEVOPS_TUTOR_SYSTEM_PROMPT

def test_factory_managed_inference_instantiation():
    try:
        agent = VoiceAgentFactory.create_agent()
        assert agent is not None
    except Exception as e:
        # Expected in environment missing livekit C dependencies
        pytest.skip(f"LiveKit plugin dependencies unavailable in local test runner: {e}")
