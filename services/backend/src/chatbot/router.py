# services/backend/src/chatbot/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from functools import lru_cache
import logging
import pandas as pd

from src.auth.session_manager import Sessions
from src.chatbot.agent import SurveyChatAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatIn(BaseModel):
    message: str
    lang: Optional[str] = "en"  # default to English

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
    Resolve the already-formatted surveys DataFrame the SAME WAY
    your visualization endpoints do. Tries (in order):
    - a module-level `surveys_df` variable
    - a `load_surveys_data()` function
    - returns None if neither exists
    """
    try:
        # 1) Your project often exposes it directly:
        from src.utils.data_loader import surveys_df  # noqa: F401
        if 'surveys_df' in locals() and surveys_df is not None:
            logger.info("[chatbot] Reusing surveys_df from data_loader")
            return surveys_df
    except Exception:
        pass

    try:
        # 2) Or via a loader function:
        from src.utils.data_loader import load_surveys_data  # type: ignore
        df = load_surveys_data()
        logger.info(f"[chatbot] Loaded surveys_df via load_surveys_data() ({len(df)}x{len(df.columns)})")
        return df
    except Exception as e:
        logger.warning(f"[chatbot] Could not get surveys_df from data_loader: {e}")

    logger.warning("[chatbot] surveys_df unavailable; agent will fall back to DATASET_PATH if set.")
    return None

# Instantiate the agent ONCE, injecting the resolved df
_agent = SurveyChatAgent(surveys_df=_get_surveys_df())

@router.post("", response_model=ChatOut)
def chat(body: ChatIn, sess=Depends(_require_session)):
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    try:
        ans = _agent.answer(body.message.strip(), lang=(body.lang or "en"))
        return ChatOut(answer=ans)
    except Exception:
        logger.exception("chatbot failure")
        raise HTTPException(status_code=500, detail="Chatbot error")

# Optional: quick health to debug in prod
@router.get("/health")
def chat_health():
    has_df = _agent.df is not None
    cols = list(_agent.df.columns)[:8] if has_df else []
    return {"has_df": has_df, "n_rows": int(len(_agent.df)) if has_df else 0, "sample_cols": cols}
