"""LiveKit agent worker for the DevOps voice tutor.

One job == one tutoring session. The job reads the learner's chosen subject
from Redis, greets them, and records every conversation turn back to Redis.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Callable, Coroutine
from typing import Any

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.llm import ChatMessage
from livekit.agents.voice import AgentSession
from livekit.agents.voice.events import ConversationItemAddedEvent

from agent.src import metrics
from agent.src.factory import VoiceAgentFactory
from agent.src.tutor_prompts import (
    GREETING_INSTRUCTIONS,
    SUMMARY_PROMPT,
    build_resume_greeting,
)
from agent.src.visual_tags import VisualTag
from shared.state import AsyncRedisSessionRepository, extract_session_id

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

#: Data messages are published under this topic so the browser can tell visual
#: payloads apart from anything else on the room's data channel.
VISUAL_DATA_TOPIC = "visual"

AGENT_METRICS_PORT = 8001

Spawn = Callable[[Coroutine[Any, Any, Any]], None]


async def generate_session_summary(
    llm_instance: Any,
    turns: list[dict[str, Any]],
    subject: str | None = None,
) -> str:
    """Generates a concise 1-line summary using the agent's LLM or a rule-based fallback."""
    if not turns:
        return f"Discussion on {subject or 'DevOps'}"

    sample_turns = turns[-6:]
    dialogue_snippet = "\n".join(
        f"{t.get('role', 'speaker')}: {t.get('text', '')}" for t in sample_turns
    )

    try:
        chat_ctx = llm.ChatContext()
        chat_ctx.add_message(role="system", content=SUMMARY_PROMPT)
        chat_ctx.add_message(
            role="user",
            content=f"Subject: {subject or 'DevOps'}\nDialogue:\n{dialogue_snippet}",
        )
        stream = llm_instance.chat(chat_ctx=chat_ctx)
        chunks = []
        async for chunk in stream:
            if chunk.delta and chunk.delta.content:
                chunks.append(chunk.delta.content)
        summary = "".join(chunks).strip().strip('"').strip("'")
        if summary:
            return summary
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM summarization failed, using rule-based fallback: %s", exc)

    first_user_turn = next((t.get("text", "") for t in turns if t.get("role") == "user"), "")
    if first_user_turn:
        clean_first = first_user_turn[:40].strip()
        return f"{subject or 'DevOps'}: {clean_first}"
    return f"Discussion on {subject or 'DevOps'}"


def make_visual_publisher(room: rtc.Room) -> Callable[[VisualTag], Coroutine[Any, Any, None]]:
    """Publishes one visual tag to the room's data channel."""

    async def publish(tag: VisualTag) -> None:
        payload = json.dumps(tag.to_payload()).encode("utf-8")
        try:
            await room.local_participant.publish_data(
                payload, reliable=True, topic=VISUAL_DATA_TOPIC
            )
        except Exception as exc:  # noqa: BLE001 - a dropped visual must not end the lesson
            logger.warning("Could not publish %s visual: %s", tag.type, exc)

    return publish


def make_turn_recorder(
    session_id: str,
    repository: AsyncRedisSessionRepository,
    spawn: Spawn,
) -> Callable[[ConversationItemAddedEvent], None]:
    """Builds the `conversation_item_added` handler.

    Persists each user/assistant turn to `session:<room>:history` and records
    the turn metrics the dashboard plots. The handler itself is synchronous
    (the SDK emits events synchronously), so the Redis write is handed to
    `spawn`, which keeps a reference to the resulting task.
    """

    def on_conversation_item(event: ConversationItemAddedEvent) -> None:
        item = event.item
        # Agent handoffs also arrive on this event; they are not turns.
        if not isinstance(item, ChatMessage) or item.role not in ("user", "assistant"):
            return

        if item.role == "assistant":
            latency_seconds = item.metrics.get("e2e_latency")
            if latency_seconds is not None:
                metrics.E2E_LATENCY_MS.observe(latency_seconds * 1000)
            if item.interrupted:
                metrics.INTERRUPTIONS.inc()

        text = (item.text_content or "").strip()
        if not text:
            return

        spawn(
            repository.append_turn(
                session_id,
                role=item.role,
                text=text,
                interrupted=item.interrupted,
                timestamp=item.created_at,
            )
        )

    return on_conversation_item


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    room_name = ctx.room.name
    session_id = extract_session_id(room_name)
    logger.info("Agent joined room %s (session %s)", room_name, session_id)

    repository = AsyncRedisSessionRepository(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )

    # Strong references, so a Redis write is never garbage-collected mid-flight.
    pending: set[asyncio.Task[Any]] = set()

    def spawn(coro: Coroutine[Any, Any, Any]) -> None:
        task = asyncio.create_task(coro)
        pending.add(task)
        task.add_done_callback(pending.discard)

    subject = await repository.get_subject(session_id)
    agent = VoiceAgentFactory.create_agent(
        subject=subject,
        visual_sink=make_visual_publisher(ctx.room),
    )

    metrics.ACTIVE_SESSIONS.inc()

    async def on_shutdown() -> None:
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        try:
            turns = await repository.get_history(session_id)
            if len(turns) >= 2:
                summary = await generate_session_summary(agent.llm, turns, subject)
                if summary:
                    await repository.update_summary(session_id, summary)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not generate summary on shutdown for %s: %s", session_id, exc)
        await repository.end_session(session_id)
        await repository.aclose()
        metrics.ACTIVE_SESSIONS.dec()
        logger.info("Session %s ended (room %s)", session_id, room_name)

    ctx.add_shutdown_callback(on_shutdown)

    session = AgentSession()
    session.on("conversation_item_added", make_turn_recorder(session_id, repository, spawn))

    prior_turns = await repository.get_history(session_id)
    if prior_turns:
        logger.info("Resuming session %s with %d prior turns", session_id, len(prior_turns))
        restored_ctx = llm.ChatContext()
        for turn in prior_turns:
            role = turn.get("role")
            text = turn.get("text", "")
            if role in ("user", "assistant") and text:
                session.history.add_message(role=role, content=text)
                restored_ctx.add_message(role=role, content=text)
        await agent.update_chat_ctx(restored_ctx)

    await session.start(agent, room=ctx.room)

    # Speak first: resume greeting if continuing a session, otherwise initial greeting.
    if prior_turns:
        await session.generate_reply(instructions=build_resume_greeting(subject))
    else:
        await session.generate_reply(instructions=GREETING_INSTRUCTIONS)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Exposes /metrics on this port and aggregates samples written by
            # each job process into the multiprocess directory.
            prometheus_port=AGENT_METRICS_PORT,
            prometheus_multiproc_dir=metrics.PROMETHEUS_MULTIPROC_DIR,
        )
    )
