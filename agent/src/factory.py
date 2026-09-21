"""Builds the Socratic DevOps tutor agent on LiveKit Inference."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterable, Awaitable, Callable

from livekit.agents import inference, llm, voice
from livekit.agents.voice import ModelSettings

from agent.src.tutor_prompts import build_instructions
from agent.src.visual_tags import VisualTag, VisualTagFilter

logger = logging.getLogger(__name__)

# Defaults are IDs documented for LiveKit Inference at
# https://docs.livekit.io/agents/models/ and present in the livekit-agents
# 1.8.2 type literals (`livekit/agents/inference/{stt,llm,tts}.py`). The older
# `deepgram/flux-general` and `cartesia/sonic` still appear in those literals
# but are no longer the documented IDs, so they are not used as defaults.
DEFAULT_STT_MODEL = "deepgram/flux-general-en"
DEFAULT_LLM_MODEL = "openai/gpt-4o-mini"
DEFAULT_TTS_MODEL = "cartesia/sonic-3"

#: Awaited with each tag the tutor emits, so the browser can render it.
VisualSink = Callable[[VisualTag], Awaitable[None]]


class DevOpsTutorAgent(voice.Agent):
    """Tutor agent that lifts visual tags out of the response exactly once.

    Stripping happens in `llm_node`, upstream of everything else, so the TTS
    input, the transcript forwarded to the browser and the chat context that
    gets persisted to Redis all see the same clean text. That is why the
    frontend needs no parser of its own.
    """

    def __init__(
        self,
        *,
        instructions: str,
        stt: inference.STT,
        llm: inference.LLM,
        tts: inference.TTS,
        visual_sink: VisualSink | None = None,
    ) -> None:
        super().__init__(instructions=instructions, stt=stt, llm=llm, tts=tts)
        self._visual_sink = visual_sink

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk | str]:
        tag_filter = VisualTagFilter()

        async for chunk in voice.Agent.default.llm_node(self, chat_ctx, tools, model_settings):
            if isinstance(chunk, str):
                text, tags = tag_filter.feed(chunk)
                await self._publish(tags)
                if text:
                    yield text
            elif isinstance(chunk, llm.ChatChunk) and chunk.delta and chunk.delta.content:
                text, tags = tag_filter.feed(chunk.delta.content)
                await self._publish(tags)
                # Keep the chunk (it may also carry tool calls or usage) and
                # replace only its text.
                yield chunk.model_copy(
                    update={"delta": chunk.delta.model_copy(update={"content": text or None})}
                )
            else:
                yield chunk

        trailing = tag_filter.flush()
        if trailing:
            yield trailing

    async def _publish(self, tags: list[VisualTag]) -> None:
        if not self._visual_sink:
            return
        for tag in tags:
            await self._visual_sink(tag)


class VoiceAgentFactory:
    """Creates the tutor agent using LiveKit Inference for STT, LLM and TTS."""

    @staticmethod
    def create_agent(
        subject: str | None = None,
        visual_sink: VisualSink | None = None,
    ) -> DevOpsTutorAgent:
        stt_model = os.getenv("STT_MODEL", DEFAULT_STT_MODEL)
        llm_model = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
        tts_model = os.getenv("TTS_MODEL", DEFAULT_TTS_MODEL)
        logger.info(
            "Creating DevOps tutor agent (stt=%s llm=%s tts=%s subject=%s)",
            stt_model,
            llm_model,
            tts_model,
            subject or "general DevOps",
        )

        return DevOpsTutorAgent(
            instructions=build_instructions(subject),
            stt=inference.STT(model=stt_model),
            llm=inference.LLM(model=llm_model),
            tts=inference.TTS(model=tts_model),
            visual_sink=visual_sink,
        )
