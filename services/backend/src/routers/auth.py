from __future__ import annotations
import re, time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, Query, Depends
from pydantic import BaseModel

from src.auth.schemas import LoginIn, UserCreateIn, UserUpdateIn, MsgOut
from src.auth.passwords import validate_password, hash_password, verify_password
from src.auth.session_manager import Sessions

router = APIRouter(prefix="/api", tags=["auth"])

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24  # 1 day


# ---------- utils ----------

def _sanitize_username(u: str) -> str:
    u2 = re.sub(r"[^\w\-.]", "", (u or "").strip())
    if len(u2) < 3 or len(u2) > 64:
        raise HTTPException(status_code=400, detail="Invalid username length")
    return u2


def _public_user(d: dict) -> dict:
    out = dict(d)
    out.pop("hashed_password", None)
    return out


# ---------- models for responses ----------

class LoginMsg(BaseModel):
    message: str = "Login successful"


class MeOut(BaseModel):
    username: str
    full_name: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True
    last_login: Optional[str] = None


# ---------- AUTH (cookie-based) ----------

@router.post("/login", response_model=LoginMsg)
def login(body: LoginIn, response: Response):
    username = _sanitize_username(body.username)

    if Sessions.is_locked(username):
        raise HTTPException(status_code=403, detail="Account temporarily locked due to failed attempts.")

    u = Sessions.get_user(username)
    # Your storage had "is_active" sometimes as "1" string; normalize to bool
    is_active = u and (u.get("is_active") in (True, 1, "1", "true", "True"))
    if not u or not is_active:
        Sessions.record_failed_attempt(username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(body.password, u.get("hashed_password", "")):
        Sessions.record_failed_attempt(username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # success
    Sessions.clear_attempts(username)
    Sessions.update_user(username, last_login=str(int(time.time())))

    # create session and set HttpOnly cookie
    session_id = Sessions.create_session(username, _public_user(u))

    # In dev you can keep secure=False; in prod behind HTTPS set secure=True
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return LoginMsg()


@router.post("/logout", response_model=MsgOut)
def logout(request: Request, response: Response):
    # Try to get the cookie
    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if sid:
        Sessions.delete_session(sid)
    # Always delete cookie on client
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return MsgOut(message="Logged out")


@router.get("/me", response_model=MeOut)
def me(request: Request):
    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if not sid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    sess = Sessions.get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user_json = sess.get("user_json") or {}
    # minimal normalization for response model
    return MeOut(
        username=user_json.get("username") or user_json.get("user") or "",
        full_name=user_json.get("full_name"),
        is_admin=bool(user_json.get("is_admin")),
        is_active=bool(user_json.get("is_active", True)),
        last_login=user_json.get("last_login"),
    )
