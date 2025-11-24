# src/auth/redis_client.py
import os
import time
import redis
from dotenv import load_dotenv

# Load .env if present (safe on host and in container)
load_dotenv()

class RedisConn:
    _client = None
    _url = None

    @classmethod
    # SINGLETON RE
    def client(cls) -> redis.Redis:
        if cls._client is not None:
            return cls._client

        # Prefer env; default to docker service name
        url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        cls._url = url

        # Helpful log once
        print(f"[auth] Connecting to Redis at {url}", flush=True)

        # Robust connect with retries
        retries = int(os.getenv("REDIS_CONNECT_RETRIES", "20"))
        delay = float(os.getenv("REDIS_CONNECT_BACKOFF", "0.5"))

        last_err = None
        for i in range(1, retries + 1):
            try:
                client = redis.from_url(url, decode_responses=True)
                client.ping()
                cls._client = client
                print("[auth] Redis connected.", flush=True)
                return cls._client
            except Exception as e:
                last_err = e
                print(f"[auth] Redis attempt {i}/{retries} failed: {e}", flush=True)
                time.sleep(delay)

        # Fail with a readable error
        raise RuntimeError(f"[auth] Could not connect to Redis at {url}: {last_err}")
