# services/backend/src/chatbot/init_db.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.chatbot.config import ChatbotConfig
from src.chatbot.chroma_client import ChromaClient
from src.chatbot.markdown_splitter import MarkdownSplitter

logger = logging.getLogger(__name__)


def init_chatbot_db(
    config: ChatbotConfig,
    *,
    documentation_path: Optional[str] = None,
    force_rebuild: bool = False,
) -> ChromaClient:
    """
    Ensure the Chroma DB is initialized with dataset documentation chunks.

    - Reads dataset_documentation.md
    - Splits into chunks by headers
    - Adds to Chroma if empty (or if force_rebuild=True)
    """
    chroma = ChromaClient(
        persist_path=config.persist_path,
        collection_name=config.collection_name,
    )

    if force_rebuild:
        logger.warning("[chatbot] force_rebuild=True requested. Rebuilding collection.")
        try:
            chroma.collection.delete(where={})
        except Exception:
            # Some chroma versions don't support delete(where={}) the same way
            pass

    if not force_rebuild and not chroma.is_empty():
        logger.info("[chatbot] Chroma collection already initialized. Skipping.")
        return chroma

    doc_path = Path(documentation_path) if documentation_path else Path(__file__).with_name("dataset_documentation.md")
    if not doc_path.exists():
        raise FileNotFoundError(f"dataset_documentation.md not found at: {doc_path}")

    md_text = doc_path.read_text(encoding="utf-8")

    splitter = MarkdownSplitter()
    docs = splitter.split_text(md_text)

    texts = []
    metas = []
    for d in docs:
        texts.append(d.page_content)
        # keep section headers in metadata when available
        metas.append(d.metadata or {"source": str(doc_path)})

    chroma.add_documents(texts=texts, metadatas=metas)
    logger.info(f"[chatbot] Added {len(texts)} documentation chunks to Chroma")

    return chroma


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = ChatbotConfig.from_env()
    init_chatbot_db(cfg, force_rebuild=False)
    print("Chroma DB initialized.")
