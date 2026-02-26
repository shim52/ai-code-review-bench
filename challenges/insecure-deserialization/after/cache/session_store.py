import pickle

import redis


class SessionStore:
    """Session store backed by Redis with pickle serialization for richer data support."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url)

    def set(self, session_id: str, data: dict, ttl: int = 3600) -> None:
        """Store session data using pickle for complex object support."""
        serialized = pickle.dumps(data)
        self.client.setex(session_id, ttl, serialized)

    def get(self, session_id: str) -> dict | None:
        """Retrieve and deserialize session data."""
        raw = self.client.get(session_id)
        if raw is None:
            return None
        return pickle.loads(raw)

    def delete(self, session_id: str) -> None:
        """Remove session data."""
        self.client.delete(session_id)

    def get_or_create(self, session_id: str, default: dict | None = None) -> dict:
        """Get existing session or create with defaults."""
        existing = self.get(session_id)
        if existing is not None:
            return existing
        data = default or {}
        self.set(session_id, data)
        return data
