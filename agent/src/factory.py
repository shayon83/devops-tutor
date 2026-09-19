import os
import logging
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class VoicePipelineFactory:
    @staticmethod
    def create_agent(mode: str = "realtime"):
        mode = mode.lower()
        logger.info(f"Creating Voice Agent in mode: '{mode}'")

        if mode in ("realtime", "livekit_managed"):
            try:
                from livekit.agents.multimodal import MultimodalAgent
                from livekit.plugins import openai

                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                azure_key = os.getenv("AZURE_OPENAI_API_KEY")

                if azure_endpoint and azure_key:
                    logger.info("Using Azure OpenAI / Microsoft Foundry Realtime Model")
                    model = openai.realtime.RealtimeModel.with_azure(
                        azure_endpoint=azure_endpoint,
                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini-realtime-preview"),
                        api_key=azure_key,
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview"),
                        instructions=DEVOPS_TUTOR_SYSTEM_PROMPT,
                        voice="alloy"
                    )
                else:
                    logger.info("Using Standard OpenAI / LiveKit Managed Realtime Model")
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
