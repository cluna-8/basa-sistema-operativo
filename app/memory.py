import os
import redis as redis_lib
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore

_checkpointer: RedisSaver | None = None
_store: RedisStore | None = None


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_checkpointer() -> RedisSaver:
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = RedisSaver(_redis_url())
        _checkpointer.setup()
    return _checkpointer


def get_store() -> RedisStore:
    global _store
    if _store is None:
        client = redis_lib.from_url(_redis_url())
        _store = RedisStore(client)
        _store.setup()
    return _store
