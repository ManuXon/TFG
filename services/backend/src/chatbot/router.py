# services/backend/src/chatbot/router.py
from __future__ import annotations

import importlib
import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.auth.session_manager import Sessions
from src.chatbot.agent import SurveyChatAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatIn(BaseModel):
    message: str
    lang: Optional[str] = "en"


class ChatOut(BaseModel):
    answer: str


def _require_session(request: Request) -> dict:
    sid = request.cookies.get("session")
    if not sid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    sess = Sessions.get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return sess


@lru_cache(maxsize=1)
def _get_surveys_df() -> Optional[pd.DataFrame]:
    """
    Robustly reuse the same surveys dataframe your app uses.
    Avoid importing non-existent symbols directly.
    """
    try:
        m = importlib.import_module("src.utils.data_loader")
    except Exception as e:
        logger.warning("[chatbot] cannot import src.utils.data_loader: %s", e)
        return None

    # Common patterns: a module-level dataframe
    for attr in ("surveys_df", "SURVEYS_DF"):
        df = getattr(m, attr, None)
        if isinstance(df, pd.DataFrame) and not df.empty:
            logger.info("[chatbot] using data_loader.%s (%sx%s)", attr, len(df), len(df.columns))
            return df

    # Common patterns: a function that returns the dataframe
    for fn in ("load_surveys_data", "get_surveys_df", "load_data"):
        f = getattr(m, fn, None)
        if callable(f):
            try:
                df = f()
                if isinstance(df, pd.DataFrame) and not df.empty:
                    logger.info("[chatbot] using data_loader.%s() (%sx%s)", fn, len(df), len(df.columns))
                    return df
            except Exception as e:
                logger.warning("[chatbot] data_loader.%s() failed: %s", fn, e)

    logger.warning("[chatbot] surveys_df unavailable; chatbot will still run but analysis may be limited.")
    return None


@lru_cache(maxsize=1)
def _get_agent() -> SurveyChatAgent:
    return SurveyChatAgent(surveys_df=_get_surveys_df())


def _append_chat_log(sid: str, user_msg: str, answer: str, lang: str) -> None:
    try:
        Path("logs").mkdir(parents=True, exist_ok=True)
        p = Path("logs/chatbot.jsonl")
        rec = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "session": sid,
            "lang": lang,
            "user": user_msg,
            "assistant": answer,
        }
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("[chatbot] could not write log: %s", e)


@router.post("", response_model=ChatOut)
def chat(body: ChatIn, request: Request, sess=Depends(_require_session)):
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    sid = request.cookies.get("session") or "unknown"
    lang = (body.lang or "en").strip() or "en"

    # keep short history per session (optional)
    history: List[Dict[str, str]] = sess.setdefault("chat_history", [])
    history.append({"role": "user", "content": msg})
    history[:] = history[-12:]  # keep last N

    try:
        agent = _get_agent()
        ans = agent.answer(msg, lang=lang, chat_history=history)
        history.append({"role": "assistant", "content": ans})
        history[:] = history[-12:]
        _append_chat_log(sid, msg, ans, lang)
        return ChatOut(answer=ans)
    except Exception:
        logger.exception("chatbot failure")
        raise HTTPException(status_code=500, detail="Chatbot error")


@router.get("/health")
def chat_health():
    agent = _get_agent()
    has_df = agent.df is not None
    cols = list(agent.df.columns)[:8] if has_df else []
    return {"has_df": has_df, "n_rows": int(len(agent.df)) if has_df else 0, "sample_cols": cols}
