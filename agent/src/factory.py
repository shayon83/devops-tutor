import os
import logging
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def is_valid_key(val: str | None) -> bool:
    if not val:
        return False
    val = val.strip()
    if not val or val.startswith("your_") or "your-resource-name" in val or val.startswith("your-"):
        return False
    return True

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
                openai_key = os.getenv("OPENAI_API_KEY")

                if is_valid_key(azure_endpoint) and is_valid_key(azure_key):
                    logger.info("Using Azure OpenAI / Microsoft Foundry Realtime Model")
                    model = openai.realtime.RealtimeModel.with_azure(
                        azure_endpoint=azure_endpoint,
                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini-realtime-preview"),
                        api_key=azure_key,
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview"),
                        voice="alloy"
                    )
                elif is_valid_key(openai_key):
                    logger.info("Using Standard OpenAI Realtime Model")
                    model = openai.realtime.RealtimeModel(
                        api_key=openai_key,
                        voice="alloy"
                    )
                else:
                    logger.error("❌ NO VALID OPENAI OR AZURE OPENAI API KEY DETECTED IN .env!")
                    logger.error("Please set OPENAI_API_KEY or AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT in your .env file.")
                    raise ValueError("Missing valid OPENAI_API_KEY or AZURE_OPENAI_API_KEY in .env.")

                return Agent(instructions=DEVOPS_TUTOR_SYSTEM_PROMPT, llm=model)
            except Exception as e:
                logger.warning(f"Failed to instantiate Realtime model, falling back to modular: {e}")

        # Modular Pipeline Mode (Supported for both local worker and cloud dispatch)
        try:
            from livekit.plugins import silero

            deepgram_key = os.getenv("DEEPGRAM_API_KEY")
            elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
            openai_key = os.getenv("OPENAI_API_KEY")

            if is_valid_key(deepgram_key):
                from livekit.plugins import deepgram
                stt = deepgram.STT(api_key=deepgram_key)
            elif is_valid_key(openai_key):
                stt = openai.STT(api_key=openai_key)
            else:
                raise ValueError("No valid STT API Key (DEEPGRAM_API_KEY or OPENAI_API_KEY) found in .env.")

            if is_valid_key(elevenlabs_key):
                from livekit.plugins import elevenlabs
                tts = elevenlabs.TTS(api_key=elevenlabs_key)
            elif is_valid_key(openai_key):
                tts = openai.TTS(api_key=openai_key, voice="alloy")
            else:
                raise ValueError("No valid TTS API Key (ELEVENLABS_API_KEY or OPENAI_API_KEY) found in .env.")

            if not is_valid_key(openai_key):
                raise ValueError("No valid OPENAI_API_KEY found in .env for modular LLM.")

            logger.info("Using Modular Pipeline")
            return Agent(
                instructions=DEVOPS_TUTOR_SYSTEM_PROMPT,
                vad=silero.VAD.load(),
                stt=stt,
                llm=openai.LLM(model="gpt-4o-mini", api_key=openai_key),
                tts=tts
            )
        except Exception as e:
            logger.error(f"Error instantiating Voice Agent: {e}")
            raise e

