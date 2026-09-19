import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    livekit_url: str = os.getenv("LIVEKIT_URL", "wss://your-livekit-server.livekit.cloud")
    livekit_api_key: str = os.getenv("LIVEKIT_API_KEY", "")
    livekit_api_secret: str = os.getenv("LIVEKIT_API_SECRET", "")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    voice_pipeline_mode: str = os.getenv("VOICE_PIPELINE_MODE", "realtime")

settings = Settings()
