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

def parse_and_strip_tags(text: str):
    clean_text = []
    tags = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i+9] == '[DIAGRAM:' or text[i:i+6] == '[YAML:' or text[i:i+6] == '[CARD:':
            start = i
            colon_idx = text.find(':', start)
            tag_type = text[start+1:colon_idx].strip().lower()
            depth = 0
            j = start
            while j < n:
                if text[j] == '[':
                    depth += 1
                elif text[j] == ']':
                    depth -= 1
                    if depth == 0:
                        content = text[colon_idx+1:j].strip()
                        tags.append((tag_type, content))
                        i = j + 1
                        break
                j += 1
            else:
                i += 1
        else:
            clean_text.append(text[i])
            i += 1
    return ''.join(clean_text).strip(), tags

async def entrypoint(ctx: JobContext):
    logger.info(f"Agent joining room: {ctx.room.name} [LiveKit Cloud Managed Inference]")
    await ctx.connect()

    agent = VoiceAgentFactory.create_agent()
    
    # Send visual payload via DataTrack
    async def send_visual_card(data_dict: dict):
        try:
            payload = json.dumps(data_dict).encode("utf-8")
            await ctx.room.local_participant.publish_data(payload, reliable=True)
        except Exception as e:
            logger.warning(f"Data track publish error: {e}")

    async def visual_tag_transform(text_stream):
        chunks = []
        async for chunk in text_stream:
            chunks.append(chunk)
        
        full_text = "".join(chunks)
        clean_text, tags = parse_and_strip_tags(full_text)

        for tag_type, content in tags:
            if tag_type == "diagram":
                asyncio.create_task(send_visual_card({"type": "diagram", "content": content}))
            elif tag_type == "yaml":
                asyncio.create_task(send_visual_card({"type": "yaml", "content": content}))
            elif tag_type == "card":
                parts = content.split("|", 1)
                title = parts[0].strip() if len(parts) > 0 else "Key Concept"
                msg = parts[1].strip() if len(parts) > 1 else content
                asyncio.create_task(send_visual_card({"type": "card", "title": title, "message": msg}))

        yield clean_text

    await asyncio.sleep(1)
    await send_visual_card({
        "type": "welcome",
        "title": "Welcome to DevOps Voice Tutor!",
        "message": "Say hello to begin your interactive Socratic SRE session."
    })

    session = AgentSession(
        tts_text_transforms=[visual_tag_transform, "filter_markdown", "filter_emoji"]
    )
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
