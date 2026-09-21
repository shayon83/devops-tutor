"""The agent must be constructible with the configured models."""

from __future__ import annotations

import typing

import pytest
from livekit.agents.inference.llm import LLMModels
from livekit.agents.inference.stt import STTModels
from livekit.agents.inference.tts import TTSModels

from agent.src.factory import (
    DEFAULT_LLM_MODEL,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DevOpsTutorAgent,
    VoiceAgentFactory,
)
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT


def _literal_values(annotation) -> set[str]:
    """Flattens a union of `Literal[...]` into the set of strings it allows."""
    values: set[str] = set()
    args = typing.get_args(annotation)
    for arg in args:
        if isinstance(arg, str):
            values.add(arg)
        else:
            values |= _literal_values(arg)
    return values


def test_system_prompt_contains_socratic_instructions():
    assert "Socratic Voice Tutor" in DEVOPS_TUTOR_SYSTEM_PROMPT
    assert "[DIAGRAM:" in DEVOPS_TUTOR_SYSTEM_PROMPT
    assert "[YAML:" in DEVOPS_TUTOR_SYSTEM_PROMPT


@pytest.mark.parametrize(
    ("model_id", "annotation"),
    [
        (DEFAULT_STT_MODEL, STTModels),
        (DEFAULT_LLM_MODEL, LLMModels),
        (DEFAULT_TTS_MODEL, TTSModels),
    ],
)
def test_default_model_ids_exist_in_the_sdk(model_id, annotation):
    """Guards against model names that were guessed rather than looked up."""
    assert model_id in _literal_values(annotation)


def test_agent_is_constructed_with_the_configured_models():
    # No try/except: if the agent cannot be built, this test fails. That is
    # the point -- the previous version turned any exception into a skip.
    agent = VoiceAgentFactory.create_agent()

    assert isinstance(agent, DevOpsTutorAgent)
    assert agent.stt.model == DEFAULT_STT_MODEL
    assert agent.llm.model == DEFAULT_LLM_MODEL
    assert agent.tts.model == DEFAULT_TTS_MODEL


def test_model_ids_are_overridable_from_the_environment(monkeypatch):
    monkeypatch.setenv("TTS_MODEL", "cartesia/sonic-3.5")
    agent = VoiceAgentFactory.create_agent()
    assert agent.tts.model == "cartesia/sonic-3.5"


def test_subject_is_added_to_the_instructions():
    agent = VoiceAgentFactory.create_agent(subject="CI/CD & GitOps Workflows")
    assert "CI/CD & GitOps Workflows" in agent.instructions


def test_missing_subject_falls_back_to_general_devops():
    agent = VoiceAgentFactory.create_agent(subject=None)
    assert agent.instructions.strip() == DEVOPS_TUTOR_SYSTEM_PROMPT.strip()
