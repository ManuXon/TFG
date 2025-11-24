from __future__ import annotations

import os, json, secrets, time
from typing import Optional
from .redis_client import RedisConn

SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "30"))

class Sessions:
    SP = "auth:session:"
    UP = "auth:user:"
    UX = "auth:users"            # set of usernames
    LA = "auth:attempts:"        # failed login attempts per username

    @staticmethod
    def _now() -> int:
        return int(time.time())

    # --------- USERS (stored as hashes) ----------

    @classmethod
    def user_key(cls, username: str) -> str:
        return f"{cls.UP}{username}"

    @classmethod
    def user_exists(cls, username: str) -> bool:
        return RedisConn.client().exists(cls.user_key(username)) == 1

    @classmethod
    def create_user(cls, username: str, hashed_password: str, full_name: str|None, is_admin: bool, is_active: bool):
        r = RedisConn.client()
        pipe = r.pipeline()
        pipe.hset(cls.user_key(username), mapping={
            "username": username,
            "hashed_password": hashed_password,
            "full_name": full_name or "",
            "is_admin": "1" if is_admin else "0",
            "is_active": "1" if is_active else "0",
            "created_at": str(cls._now()),
            "last_login": "",
        })
        pipe.sadd(cls.UX, username)
        pipe.execute()

    @classmethod
    def get_user(cls, username: str) -> Optional[dict]:
        d = RedisConn.client().hgetall(cls.user_key(username))
        return d or None

    @classmethod
    def update_user(cls, username: str, **fields):
        r = RedisConn.client()
        allowed = {"full_name","is_admin","is_active","hashed_password","last_login"}
        mapping = {}
        for k,v in fields.items():
            if k not in allowed: continue
            if k in ("is_admin","is_active"): v = "1" if bool(v) else "0"
            mapping[k] = v if v is not None else ""
        if mapping:
            r.hset(cls.user_key(username), mapping=mapping)

    @classmethod
    def delete_user(cls, username: str):
        r = RedisConn.client()
        pipe = r.pipeline()
        pipe.delete(cls.user_key(username))
        # also nuke their sessions
        for tk in r.smembers(f"auth:user_sessions:{username}"):
            pipe.delete(f"{cls.SP}{tk}")
        pipe.delete(f"auth:user_sessions:{username}")
        pipe.srem(cls.UX, username)
        pipe.execute()

    @classmethod
    def list_users(cls) -> list[dict]:
        r = RedisConn.client()
        names = sorted(list(r.smembers(cls.UX)))
        out = []
        for u in names:
            d = r.hgetall(cls.user_key(u))
            if d:
                d.pop("hashed_password", None)
                out.append(d)
        return out

    # --------- SESSIONS ----------

    @classmethod
    def create_session(cls, username: str, user_payload: dict) -> str:
        r = RedisConn.client()
        token = secrets.token_urlsafe(32)
        key = f"{cls.SP}{token}"
        r.hset(key, mapping={
            "username": username,
            "user_json": json.dumps(user_payload),
            "created_at": str(cls._now()),
        })
        r.expire(key, SESSION_TTL_HOURS * 3600)
        r.sadd(f"auth:user_sessions:{username}", token)
        r.expire(f"auth:user_sessions:{username}", SESSION_TTL_HOURS * 3600)
        return token

    @classmethod
    def get_session(cls, token: str) -> Optional[dict]:
        r = RedisConn.client()
        key = f"{cls.SP}{token}"
        d = r.hgetall(key)
        if not d:
            return None
        # sliding expiration
        r.expire(key, SESSION_TTL_HOURS * 3600)
        d["user_json"] = json.loads(d.get("user_json","{}"))
        return d

    @classmethod
    def delete_session(cls, token: str):
        r = RedisConn.client()
        key = f"{cls.SP}{token}"
        username = r.hget(key, "username")
        pipe = r.pipeline()
        pipe.delete(key)
        if username:
            pipe.srem(f"auth:user_sessions:{username}", token)
        pipe.execute()

    @classmethod
    def revoke_user_sessions(cls, username: str):
        r = RedisConn.client()
        k = f"auth:user_sessions:{username}"
        tks = r.smembers(k)
        pipe = r.pipeline()
        for tk in tks:
            pipe.delete(f"{cls.SP}{tk}")
        pipe.delete(k)
        pipe.execute()

    # --------- LOCKOUT ----------

    @classmethod
    def record_failed_attempt(cls, username: str) -> int:
        r = RedisConn.client()
        key = f"{cls.LA}{username}"
        n = r.incr(key)
        if n == 1:
            r.expire(key, LOCKOUT_MINUTES * 60)
        return n

    @classmethod
    def clear_attempts(cls, username: str):
        RedisConn.client().delete(f"{cls.LA}{username}")

    @classmethod
    def is_locked(cls, username: str) -> bool:
        r = RedisConn.client()
        key = f"{cls.LA}{username}"
        n = r.get(key)
        if not n: return False
        return int(n) >= MAX_LOGIN_ATTEMPTS
