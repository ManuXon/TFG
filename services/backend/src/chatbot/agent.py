# services/backend/src/chatbot/agent.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from src.chatbot.config import ChatbotConfig
from src.chatbot.chatbot_client import ChatbotClient

logger = logging.getLogger(__name__)


class SurveyChatAgent:
    """
    Thin wrapper used by router.py.
    Keeps your import style: from src.chatbot.agent import SurveyChatAgent
    """

    def __init__(self, surveys_df: Optional[pd.DataFrame] = None):
        self.config = ChatbotConfig.from_env()
        self.df = surveys_df

        # IMPORTANT: keep constructor compatible even if chroma is not ready.
        chroma_client = None
        try:
            from src.chatbot.chroma_client import ChromaClient  # optional

            chroma_client = ChromaClient(
                persist_path=self.config.persist_path,
                collection_name=self.config.collection_name,
                api_key=self.config.openai_api_key,
            )
        except Exception as e:
            logger.warning("[chatbot] Chroma disabled (ok). Reason: %s", e)

        self.client = ChatbotClient(
            config=self.config,
            surveys_df=surveys_df,
            chroma_client=chroma_client,
        )

    def answer(
        self,
        message: str,
        lang: str = "en",
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        # Call whichever method exists (prevents your current crash forever)
        if hasattr(self.client, "process_query"):
            text, _sources = self.client.process_query(message, chat_history=chat_history, lang=lang)
            return text

        if hasattr(self.client, "query"):
            text, _sources = self.client.query(message, chat_history=chat_history, lang=lang)
            return text

        raise RuntimeError("ChatbotClient must implement process_query() or query()")
