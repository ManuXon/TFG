# services/backend/src/chatbot/audit_log.py
from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict


_LOGGER_NAME = "chatbot.audit"
_DEFAULT_PATH = "logs/chatbot_audit.jsonl"


def get_chat_audit_logger() -> logging.Logger:
    """
    JSONL audit logger (question/answer/metadata). Rotates automatically.
    Safe to import anywhere; only configures once per process.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)
    logger.propagate = False  # don't duplicate into root logger

    log_path = os.getenv("CHATBOT_LOG_PATH", _DEFAULT_PATH)
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        filename=str(p),
        maxBytes=int(os.getenv("CHATBOT_LOG_MAX_BYTES", str(5 * 1024 * 1024))),  # 5MB
        backupCount=int(os.getenv("CHATBOT_LOG_BACKUP_COUNT", "5")),
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)

    # Store raw JSON strings (one per line)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger


def audit_event(logger: logging.Logger, payload: Dict[str, Any]) -> None:
    """
    Write one JSON line. Never crash the request if logging fails.
    """
    try:
        logger.info(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass
