"""
Login rate limiting: per-IP attempt counting with Redis (multi-worker) or in-memory fallback.
"""
import logging
import time

from fastapi import HTTPException

from .config import settings

logger = logging.getLogger(__name__)

# In-memory fallback when REDIS_URL is not set (single worker only)
_memory_store: dict[str, list[float]] = {}

# Lazy Redis client (used when REDIS_URL is set)
_redis_client = None

KEY_PREFIX = "argos:login:"


def _get_redis():
    global _redis_client
    if settings.REDIS_URL and _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
        except Exception as e:
            logger.warning("Redis connection failed for rate limit: %s", e)
            return None
    return _redis_client


def _check_memory(identifier: str) -> None:
    """In-memory rate limit (single process only)."""
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.LOGIN_RATE_LIMIT_PER_MINUTE
    now = time.time()
    start = now - window
    if identifier not in _memory_store:
        _memory_store[identifier] = []
    _memory_store[identifier] = [t for t in _memory_store[identifier] if t > start]
    if len(_memory_store[identifier]) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
        )
    _memory_store[identifier].append(now)


def _check_redis(identifier: str) -> None:
    """Redis-backed rate limit (works across workers/replicas)."""
    r = _get_redis()
    if r is None:
        _check_memory(identifier)
        return
    key = f"{KEY_PREFIX}{identifier}"
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.LOGIN_RATE_LIMIT_PER_MINUTE
    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        n, ttl = pipe.execute()
        if n == 1:
            r.expire(key, window)
        if n > max_attempts:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Redis rate limit check failed, falling back to in-memory: %s", e)
        _check_memory(identifier)


def check_login_rate_limit(identifier: str) -> None:
    """
    Enforce login rate limit for the given identifier (e.g. client IP).
    Raises HTTP 429 when the limit is exceeded.
    Uses Redis when REDIS_URL is set, otherwise in-memory (single worker).
    """
    if settings.REDIS_URL:
        _check_redis(identifier)
    else:
        _check_memory(identifier)
