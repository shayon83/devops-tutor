import os
import sys
import time
import json
import logging
import asyncio
from dotenv import load_dotenv

# Ensure root import paths work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from prometheus_client import start_http_server, Histogram, Counter
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession

from backend.src.session_manager import RedisSessionRepository
from agent.src.factory import VoiceAgentFactory

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

# Prometheus Metrics
VOICE_TURN_LATENCY = Histogram(
    "voice_tutor_e2e_latency_ms",
    "End-to-End Voice Response Latency in Milliseconds",
    buckets=[100, 250, 350, 500, 750, 1000, 1500, 2000]
)
INTERRUPTION_COUNTER = Counter("voice_tutor_interruptions_total", "Total Barge-in Interruptions")

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_repo = RedisSessionRepository(host=redis_host, port=redis_port)

async def entrypoint(ctx: JobContext):
    logger.info(f"Agent joining room: {ctx.room.name} [LiveKit Cloud Managed Inference]")
    await ctx.connect()

    agent = VoiceAgentFactory.create_agent()
    
    # Send welcome visual card via DataTrack
    async def send_visual_card(data_dict: dict):
        try:
            payload = json.dumps(data_dict).encode("utf-8")
            await ctx.room.local_participant.publish_data(payload, reliable=True)
        except Exception as e:
            logger.warning(f"Data track publish error: {e}")

    await asyncio.sleep(1)
    await send_visual_card({
        "type": "welcome",
        "title": "Welcome to DevOps Voice Tutor!",
        "message": "Say hello to begin your interactive Socratic SRE session."
    })

    session = AgentSession()
    await session.start(agent, room=ctx.room)

    logger.info("Agent session active and listening...")

if __name__ == "__main__":
    # Start Prometheus metric exporter on port 8001
    try:
        start_http_server(8001)
        logger.info("Agent Prometheus metrics listening on http://0.0.0.0:8001/metrics")
    except Exception as e:
        logger.warning(f"Could not start metrics server: {e}")

    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
