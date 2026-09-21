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
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatMessage
from livekit.agents.voice import AgentSession
from livekit.agents.voice.events import ConversationItemAddedEvent

from agent.src import metrics
from agent.src.factory import VoiceAgentFactory
from agent.src.tutor_prompts import GREETING_INSTRUCTIONS
from agent.src.visual_tags import VisualTag
from shared.state import AsyncRedisSessionRepository

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

#: Data messages are published under this topic so the browser can tell visual
#: payloads apart from anything else on the room's data channel.
VISUAL_DATA_TOPIC = "visual"

AGENT_METRICS_PORT = 8001

Spawn = Callable[[Coroutine[Any, Any, Any]], None]


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
    logger.info("Agent joined room %s", room_name)

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

    metrics.ACTIVE_SESSIONS.inc()

    async def on_shutdown() -> None:
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        await repository.end_session(room_name)
        await repository.aclose()
        metrics.ACTIVE_SESSIONS.dec()
        logger.info("Session %s ended", room_name)

    ctx.add_shutdown_callback(on_shutdown)

    subject = await repository.get_subject(room_name)
    agent = VoiceAgentFactory.create_agent(
        subject=subject,
        visual_sink=make_visual_publisher(ctx.room),
    )

    session = AgentSession()
    session.on("conversation_item_added", make_turn_recorder(room_name, repository, spawn))

    await session.start(agent, room=ctx.room)

    # Speak first: otherwise the learner sits in silence not knowing whether
    # the tutor connected.
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
