import os
import logging
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class VoicePipelineFactory:
    @staticmethod
    def create_agent(pipeline_mode: str = "realtime", dispatch_type: str = "local"):
        pipeline_mode = pipeline_mode.lower()
        dispatch_type = dispatch_type.lower()
        logger.info(f"Creating Voice Agent [Mode: '{pipeline_mode}', Dispatch: '{dispatch_type}']")

        from livekit.agents.voice import Agent
        from livekit.plugins import openai

        if pipeline_mode == "realtime":
            try:
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                azure_key = os.getenv("AZURE_OPENAI_API_KEY")

                if azure_endpoint and azure_key:
                    logger.info("Using Azure OpenAI / Microsoft Foundry Realtime Model")
                    model = openai.realtime.RealtimeModel.with_azure(
                        azure_endpoint=azure_endpoint,
                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini-realtime-preview"),
                        api_key=azure_key,
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview"),
                        voice="alloy"
                    )
                else:
                    logger.info("Using Standard OpenAI Realtime Model")
                    model = openai.realtime.RealtimeModel(
                        voice="alloy"
                    )
                return Agent(instructions=DEVOPS_TUTOR_SYSTEM_PROMPT, llm=model)
            except Exception as e:
                logger.warning(f"Failed to instantiate Realtime model, falling back to modular: {e}")

        # Modular Pipeline Mode (Supported for both local worker and cloud dispatch)
        try:
            from livekit.plugins import silero

            # Fallback for STT and TTS keys if Deepgram/ElevenLabs keys are missing
            if os.getenv("DEEPGRAM_API_KEY"):
                from livekit.plugins import deepgram
                stt = deepgram.STT()
            else:
                stt = openai.STT()

            if os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY"):
                from livekit.plugins import elevenlabs
                tts = elevenlabs.TTS()
            else:
                tts = openai.TTS(voice="alloy")

            logger.info("Using Modular Pipeline")
            return Agent(
                instructions=DEVOPS_TUTOR_SYSTEM_PROMPT,
                vad=silero.VAD.load(),
                stt=stt,
                llm=openai.LLM(model="gpt-4o-mini"),
                tts=tts
            )
        except Exception as e:
            logger.error(f"Error instantiating Voice Agent: {e}")
            raise e
