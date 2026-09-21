"""Turn persistence, visual publishing and cross-process metrics."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from livekit.agents import llm, voice
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.agents.voice import ModelSettings
from livekit.agents.voice.events import ConversationItemAddedEvent
from prometheus_client import REGISTRY, CollectorRegistry, multiprocess

from agent.src import metrics
from agent.src.agent import VISUAL_DATA_TOPIC, make_turn_recorder, make_visual_publisher
from agent.src.factory import VoiceAgentFactory

REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeLocalParticipant:
    def __init__(self) -> None:
        self.published: list[dict] = []

    async def publish_data(self, payload, *, reliable=True, topic="", **_kwargs):
        self.published.append({"payload": payload, "reliable": reliable, "topic": topic})


class FakeRoom:
    def __init__(self) -> None:
        self.local_participant = FakeLocalParticipant()


class FakeRepository:
    """Records what would have been written to Redis. Raises nothing."""

    def __init__(self) -> None:
        self.turns: list[dict] = []

    async def append_turn(self, session_id, role, text, interrupted=False, timestamp=None):
        turn = {
            "session_id": session_id,
            "role": role,
            "text": text,
            "interrupted": interrupted,
            "timestamp": timestamp,
        }
        self.turns.append(turn)
        return turn


class CollectingSpawn:
    """Stands in for the agent's task spawner; the test awaits explicitly."""

    def __init__(self) -> None:
        self.coros = []

    def __call__(self, coro) -> None:
        self.coros.append(coro)

    async def drain(self) -> None:
        for coro in self.coros:
            await coro
        self.coros.clear()


def _event(role: str, text: str, **kwargs) -> ConversationItemAddedEvent:
    return ConversationItemAddedEvent(
        item=ChatMessage(role=role, content=[text], **kwargs)
    )


async def test_user_and_assistant_turns_are_persisted():
    repo = FakeRepository()
    spawn = CollectingSpawn()
    handle = make_turn_recorder("devops-room-abc", repo, spawn)

    handle(_event("user", "What does OOMKilled mean?"))
    handle(_event("assistant", "Good question. What limits did you set?"))
    await spawn.drain()

    assert [(t["role"], t["text"]) for t in repo.turns] == [
        ("user", "What does OOMKilled mean?"),
        ("assistant", "Good question. What limits did you set?"),
    ]
    assert all(t["session_id"] == "devops-room-abc" for t in repo.turns)
    assert all(t["timestamp"] is not None for t in repo.turns)


async def test_empty_and_non_message_items_are_skipped():
    repo = FakeRepository()
    spawn = CollectingSpawn()
    handle = make_turn_recorder("room", repo, spawn)

    handle(_event("user", "   "))
    handle(_event("system", "you are a tutor"))
    await spawn.drain()

    assert repo.turns == []


async def test_interruption_is_recorded_on_the_turn_and_the_counter():
    repo = FakeRepository()
    spawn = CollectingSpawn()
    handle = make_turn_recorder("room", repo, spawn)

    before = REGISTRY.get_sample_value("voice_tutor_interruptions_total") or 0.0
    handle(_event("assistant", "As I was saying...", interrupted=True))
    await spawn.drain()

    assert repo.turns[0]["interrupted"] is True
    after = REGISTRY.get_sample_value("voice_tutor_interruptions_total")
    assert after == before + 1


async def test_assistant_latency_is_observed_in_milliseconds():
    repo = FakeRepository()
    spawn = CollectingSpawn()
    handle = make_turn_recorder("room", repo, spawn)

    before = REGISTRY.get_sample_value("voice_tutor_e2e_latency_ms_sum") or 0.0
    handle(_event("assistant", "Try describing the symptom.", metrics={"e2e_latency": 0.42}))
    await spawn.drain()

    after = REGISTRY.get_sample_value("voice_tutor_e2e_latency_ms_sum")
    assert after == pytest.approx(before + 420.0)


async def test_user_turn_without_metrics_does_not_touch_latency():
    repo = FakeRepository()
    spawn = CollectingSpawn()
    handle = make_turn_recorder("room", repo, spawn)

    before = REGISTRY.get_sample_value("voice_tutor_e2e_latency_ms_count") or 0.0
    handle(_event("user", "Because the container exceeded its memory limit?"))
    await spawn.drain()

    assert REGISTRY.get_sample_value("voice_tutor_e2e_latency_ms_count") == before


async def test_visuals_are_published_on_the_visual_topic():
    room = FakeRoom()
    publish = make_visual_publisher(room)

    from agent.src.visual_tags import VisualTag

    await publish(VisualTag("diagram", "graph TD; A --> B"))

    assert len(room.local_participant.published) == 1
    message = room.local_participant.published[0]
    assert message["topic"] == VISUAL_DATA_TOPIC
    assert message["reliable"] is True
    import json

    assert json.loads(message["payload"].decode()) == {
        "type": "diagram",
        "content": "graph TD; A --> B",
    }


async def test_llm_node_strips_tags_from_the_spoken_text_and_publishes_them(monkeypatch):
    """One strip, upstream of TTS, transcripts and the persisted chat context."""
    chunks = [
        "Rolling updates replace pods gradually. ",
        "What happens to in-flight requests?",
        " [DIAGRAM: graph TD; A[Old ReplicaSet] --> B[New ReplicaSet]]",
    ]

    async def fake_default_llm_node(agent, chat_ctx, tools, model_settings):
        for chunk in chunks:
            yield chunk

    monkeypatch.setattr(
        voice.Agent.default, "llm_node", staticmethod(fake_default_llm_node), raising=True
    )

    room = FakeRoom()
    agent = VoiceAgentFactory.create_agent(visual_sink=make_visual_publisher(room))

    spoken = [
        chunk
        async for chunk in agent.llm_node(ChatContext.empty(), [], ModelSettings())
        if isinstance(chunk, str)
    ]

    assert "".join(spoken).strip() == (
        "Rolling updates replace pods gradually. What happens to in-flight requests?"
    )
    assert "[DIAGRAM" not in "".join(spoken)
    assert len(room.local_participant.published) == 1
    assert room.local_participant.published[0]["topic"] == VISUAL_DATA_TOPIC


async def test_llm_node_passes_non_text_chunks_through(monkeypatch):
    usage_chunk = llm.ChatChunk(id="chunk-1", delta=llm.ChoiceDelta(role="assistant"))

    async def fake_default_llm_node(agent, chat_ctx, tools, model_settings):
        yield usage_chunk
        yield "Hello."

    monkeypatch.setattr(
        voice.Agent.default, "llm_node", staticmethod(fake_default_llm_node), raising=True
    )

    agent = VoiceAgentFactory.create_agent()
    out = [c async for c in agent.llm_node(ChatContext.empty(), [], ModelSettings())]

    assert out[0] is usage_chunk
    assert out[1] == "Hello."


def test_metrics_written_in_a_job_process_appear_in_the_parent_registry(tmp_path):
    """LiveKit Agents runs each job in its own process.

    Without prometheus multiprocess mode, a counter incremented inside a job
    never shows up on the worker's /metrics. This drives the real mechanism:
    a separate process records into the multiproc directory, and the parent
    collects it exactly the way the SDK's /metrics handler does.
    """
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from agent.src import metrics\n"
                "metrics.ACTIVE_SESSIONS.inc()\n"
                "metrics.INTERRUPTIONS.inc()\n"
                "metrics.E2E_LATENCY_MS.observe(310.0)\n"
            ),
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PROMETHEUS_MULTIPROC_DIR": str(tmp_path),
            "PYTHONPATH": str(REPO_ROOT),
        },
        capture_output=True,
        text=True,
    )
    assert child.returncode == 0, child.stderr

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry, path=str(tmp_path))

    assert registry.get_sample_value("voice_tutor_active_sessions_total") == 1.0
    assert registry.get_sample_value("voice_tutor_interruptions_total") == 1.0
    assert registry.get_sample_value("voice_tutor_e2e_latency_ms_sum") == 310.0


def test_multiproc_dir_matches_the_one_created_in_the_image():
    dockerfile = (REPO_ROOT / "agent" / "Dockerfile").read_text()
    assert metrics.PROMETHEUS_MULTIPROC_DIR in dockerfile
