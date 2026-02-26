import json

import redis


class SessionStore:
    """Simple session store backed by Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url)

    def set(self, session_id: str, data: dict, ttl: int = 3600) -> None:
        """Store session data as JSON."""
        serialized = json.dumps(data)
        self.client.setex(session_id, ttl, serialized)

    def get(self, session_id: str) -> dict | None:
        """Retrieve session data."""
        raw = self.client.get(session_id)
        if raw is None:
            return None
        return json.loads(raw)

    def delete(self, session_id: str) -> None:
        """Remove session data."""
        self.client.delete(session_id)
