import logging
from livekit.agents import inference, voice
from agent.src.tutor_prompts import DEVOPS_TUTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class VoiceAgentFactory:
    """Factory for creating Socratic DevOps Voice Agent using LiveKit Cloud Managed Inference."""

    @staticmethod
    def create_agent() -> voice.Agent:
        logger.info("⚡ Creating Socratic DevOps Voice Agent [LiveKit Cloud Managed Inference]")

        return voice.Agent(
            instructions=DEVOPS_TUTOR_SYSTEM_PROMPT,
            stt=inference.STT(model="deepgram/flux-general"),
            llm=inference.LLM(model="openai/gpt-4o-mini"),
            tts=inference.TTS(model="cartesia/sonic")
        )

# Retain backward compatibility alias
VoicePipelineFactory = VoiceAgentFactory
