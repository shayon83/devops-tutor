import os
import logging
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class VoicePipelineFactory:
    @staticmethod
    def create_agent(mode: str = "realtime"):
        mode = mode.lower()
        logger.info(f"Creating Voice Agent in mode: '{mode}'")

        if mode == "realtime":
            try:
                from livekit.agents.multimodal import MultimodalAgent
                from livekit.plugins import openai
                model = openai.realtime.RealtimeModel(
                    instructions=DEVOPS_TUTOR_SYSTEM_PROMPT,
                    voice="alloy"
                )
                return MultimodalAgent(model=model)
            except Exception as e:
                logger.warning(f"Failed to instantiate Realtime model, falling back to modular: {e}")

        # Modular Pipeline Fallback (VAD -> STT -> LLM -> TTS)
        try:
            from livekit.agents import VoicePipelineAgent
            from livekit.plugins import silero, deepgram, openai, elevenlabs

            return VoicePipelineAgent(
                vad=silero.VAD.load(),
                stt=deepgram.STT(),
                llm=openai.LLM(model="gpt-4o-mini"),
                tts=elevenlabs.TTS()
            )
        except Exception as e:
            logger.error(f"Error instantiating VoicePipelineAgent: {e}")
            raise e
