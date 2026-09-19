import json
import time
import logging
from typing import Dict, Any, List, Optional
import redis

logger = logging.getLogger(__name__)

class RedisSessionRepository:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.client = None

    def create_session(self, session_id: str, user_id: str, subject: str = "DevOps") -> Dict[str, Any]:
        metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "subject": subject,
            "created_at": time.time(),
            "status": "active"
        }
        if self.client:
            try:
                self.client.hset(f"session:{session_id}:metadata", mapping=metadata)
                self.client.expire(f"session:{session_id}:metadata", 86400)
            except Exception as e:
                logger.warning(f"Redis operation skipped (offline): {e}")
        return metadata

    def append_turn(self, session_id: str, role: str, text: str) -> Dict[str, Any]:
        turn_data = {
            "role": role,
            "text": text,
            "timestamp": time.time()
        }
        if self.client:
            try:
                self.client.rpush(f"session:{session_id}:history", json.dumps(turn_data))
                self.client.expire(f"session:{session_id}:history", 86400)
            except Exception as e:
                logger.warning(f"Redis operation skipped (offline): {e}")
        return turn_data

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            raw_turns = self.client.lrange(f"session:{session_id}:history", 0, -1)
            return [json.loads(turn) for turn in raw_turns]
        except Exception as e:
            logger.warning(f"Redis operation skipped (offline): {e}")
            return []

    def save_feedback(self, session_id: str, rating_stars: int, tags: List[str], comment: Optional[str] = None) -> Dict[str, Any]:
        feedback_data = {
            "rating_stars": rating_stars,
            "tags": json.dumps(tags),
            "comment": comment or "",
            "timestamp": time.time()
        }
        if self.client:
            try:
                self.client.hset(f"session:{session_id}:feedback", mapping=feedback_data)
                self.client.expire(f"session:{session_id}:feedback", 86400)
            except Exception as e:
                logger.warning(f"Redis operation skipped (offline): {e}")
        return feedback_data

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        if not self.client:
            return {"session_id": session_id, "turns_count": 0}
        metadata = self.client.hgetall(f"session:{session_id}:metadata")
        history = self.get_history(session_id)
        feedback = self.client.hgetall(f"session:{session_id}:feedback")
        return {
            "metadata": metadata,
            "history": history,
            "feedback": feedback
        }
