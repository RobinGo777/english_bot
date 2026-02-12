"""
Redis client — stores publication history to avoid repeating content.
Uses cloud.redis.io (free tier).
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import redis

from config import REDIS_URL, HISTORY_DAYS

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


# ── History helpers ───────────────────────────────────────

def add_to_history(category: str, value: str) -> None:
    """Save a used word/topic/phrase so AI won't repeat it."""
    r = get_client()
    key = f"history:{category}"
    entry = json.dumps({"value": value, "date": datetime.utcnow().isoformat()})
    r.lpush(key, entry)
    # Keep only last 500 entries per category (more than enough for 90 days)
    r.ltrim(key, 0, 499)
    logger.info("History updated — %s: %s", category, value)


def get_history(category: str, days: int = HISTORY_DAYS) -> list[str]:
    """Return a list of used values within the last N days."""
    r = get_client()
    key = f"history:{category}"
    raw = r.lrange(key, 0, 499)
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = []
    for item in raw:
        try:
            data = json.loads(item)
            dt = datetime.fromisoformat(data["date"])
            if dt >= cutoff:
                recent.append(data["value"])
        except Exception:
            pass
    return recent


# ── Day counter helpers ───────────────────────────────────

def get_day_counter(name: str) -> int:
    """Get the current day counter (for rotation logic)."""
    r = get_client()
    val = r.get(f"counter:{name}")
    return int(val) if val else 1


def increment_day_counter(name: str) -> int:
    """Increment day counter and return new value."""
    r = get_client()
    key = f"counter:{name}"
    new_val = r.incr(key)
    return new_val


# ── Stats logging ─────────────────────────────────────────

def log_post_published(post_type: str, success: bool, error: str = "") -> None:
    r = get_client()
    entry = json.dumps({
        "type": post_type,
        "success": success,
        "error": error,
        "ts": datetime.utcnow().isoformat(),
    })
    r.lpush("stats:posts", entry)
    r.ltrim("stats:posts", 0, 999)


def ping() -> bool:
    """Check Redis connection."""
    try:
        get_client().ping()
        return True
    except Exception as e:
        logger.error("Redis ping failed: %s", e)
        return False
