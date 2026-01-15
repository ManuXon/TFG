# services/backend/src/chatbot/chatbot_client.py
from __future__ import annotations

import logging
import re
import unicodedata
import difflib
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from langchain_openai import ChatOpenAI

from src.chatbot.config import ChatbotConfig
from src.chatbot.pandas_agent import PandasDatasetAgent

logger = logging.getLogger(__name__)


class ChatbotClient:
    """
    Contract:
      - process_query(question, chat_history=None, lang="en") -> (answer_text, sources)
      - query(...) alias
    """

    def __init__(
        self,
        config: ChatbotConfig,
        surveys_df: Optional[pd.DataFrame] = None,
        chroma_client: Any = None,
    ):
        self.config = config
        self.df = surveys_df
        self.chroma_client = chroma_client

        self.llm = ChatOpenAI(
            temperature=config.temperature,
            model=config.model_name,
            api_key=config.openai_api_key,
            max_tokens=max(500, int(config.max_tokens or 500)),
        )

        self.pandas_agent = PandasDatasetAgent(
            surveys_df=surveys_df,
            dataset_path=config.dataset_path,
            api_key=config.openai_api_key,
            model_name=config.model_name,
        )

        # Precompute faculty normalization map for deterministic matching
        self._faculty_norm_to_exact: Dict[str, str] = {}
        self._faculty_exact_list: List[str] = []
        try:
            if self.df is not None and "faculty_name" in self.df.columns:
                vals = (
                    self.df["faculty_name"]
                    .dropna()
                    .astype(str)
                    .map(str.strip)
                    .unique()
                    .tolist()
                )
                self._faculty_exact_list = sorted(vals, key=lambda x: x.lower())
                for f in self._faculty_exact_list:
                    self._faculty_norm_to_exact[self._norm(f)] = f
        except Exception as e:
            logger.warning("[chatbot] Failed to build faculty map: %s", e)

        logger.info(
            "[chatbot] ChatbotClient ready. df=%s rows=%s cols=%s",
            "yes" if surveys_df is not None else "no",
            len(surveys_df) if surveys_df is not None else 0,
            len(surveys_df.columns) if surveys_df is not None else 0,
        )

    # ---------------- Normalization / matching ----------------

    def _norm(self, s: str) -> str:
        s = (s or "").strip().lower()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # drop accents
        s = s.replace("&", "and")
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _extract_faculty_exact(self, question: str) -> Optional[str]:
        """
        Return the exact faculty_name value from df that best matches what user wrote.
        Deterministic. No LLM guessing.
        """
        if not question or not self._faculty_exact_list:
            return None

        qn = self._norm(question)

        # 1) Direct substring match against known faculty names (most reliable)
        for exact in self._faculty_exact_list:
            fn = self._norm(exact)
            if fn and fn in qn:
                return exact

        # 2) Regex: capture "... faculty" mention
        m = re.search(r"(?:in|at|for|en|a|de|del|dels|dela|de la)\s+(.+?)\s+faculty\b", qn)
        cand = (m.group(1).strip() if m else "").strip()
        if cand:
            # try exact normalized map
            candn = self._norm(cand)
            if candn in self._faculty_norm_to_exact:
                return self._faculty_norm_to_exact[candn]

            # fuzzy match
            best = difflib.get_close_matches(candn, list(self._faculty_norm_to_exact.keys()), n=1, cutoff=0.75)
            if best:
                return self._faculty_norm_to_exact[best[0]]

        # 3) Fuzzy match on the whole question (last resort)
        best2 = difflib.get_close_matches(qn, list(self._faculty_norm_to_exact.keys()), n=1, cutoff=0.85)
        if best2:
            return self._faculty_norm_to_exact[best2[0]]

        return None

    def _inject_faculty_filter(self, question: str) -> str:
        """
        If the user specifies a faculty, rewrite the question so the pandas agent
        MUST filter df to that exact faculty_name.
        """
        exact = self._extract_faculty_exact(question)
        if not exact:
            return question

        # Don’t double-inject if user already included an explicit filter hint
        if "faculty_name" in (question or ""):
            return question

        injected = (
            f"IMPORTANT: The user is asking about the faculty '{exact}'. "
            f"Before computing anything, filter the DataFrame EXACTLY with:\n"
            f"df_fac = df[df['faculty_name'] == \"{exact}\"]\n"
            f"Then compute the requested comparison on df_fac (not on full df).\n\n"
            f"User question: {question}"
        )
        return injected

    # ---------------- Routing helpers ----------------

    def _should_use_pandas(self, question: str) -> bool:
        q = (question or "").strip().lower()
        if not q:
            return False

        triggers = [
            "how many", "count", "number of", "total", "responses",
            "percentage", "percent", "%", "ratio", "proportion", "share",
            "mean", "average", "median", "std", "variance", "distribution",
            "top", "rank", "most", "least",
            "more", "less", "fewer", "higher", "lower", "greater", "smaller",
            "compare", "comparison", "difference", "between", "vs", "versus",
            "by ", "per ", "group", "grouped", "filter", "subset",
            "faculty", "facult", "gender", "male", "female", "non-binary",
            "knowledge_score", "uses_score", "perceptions_score", "training_needs_score",
        ]
        return any(t in q for t in triggers)

    def _looks_like_dataset_question(self, question: str) -> bool:
        q = (question or "").lower()
        return any(x in q for x in [
            "gender", "male", "female", "males", "females",
            "how many", "count", "number of", "more", "less", "fewer",
            "compare", "difference", "percentage", "percent", "distribution",
            "mean", "average", "median", "correlation", "by faculty", "faculty",
            "knowledge_score", "uses_score", "perceptions_score", "training_needs_score",
        ])

    def _looks_like_refusal(self, answer_text: str) -> bool:
        a = (answer_text or "").lower()
        return any(x in a for x in [
            "i don't have", "i do not have", "don't have the specific data",
            "cannot determine", "unable to", "no information", "not available",
            "i'm sorry, but i don't", "i'm sorry but i don't",
            "no disposo", "no tinc", "no puc determinar", "no està disponible",
        ])

    # ---------------- Main entrypoint ----------------

    def process_query(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        lang: str = "en",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        sources: List[Dict[str, Any]] = []
        context = ""
        analysis = ""
        answer_text = ""

        try:
            # 1) Retrieval context (optional)
            try:
                if self.chroma_client is not None:
                    retriever = getattr(self.chroma_client, "create_retriever", None)
                    if callable(retriever):
                        r = retriever(k=int(self.config.num_docs or 5))
                        docs = r.invoke(question) if hasattr(r, "invoke") else r.get_relevant_documents(question)
                        for d in docs[: int(self.config.num_docs or 5)]:
                            snippet = (d.page_content or "")[:400]
                            sources.append(
                                {"source": (d.metadata or {}).get("source"), "snippet": snippet}
                            )
                        context = "\n\n".join(
                            [(d.page_content or "") for d in docs[: int(self.config.num_docs or 5)]]
                        )
            except Exception as e:
                logger.warning("[chatbot] retrieval failed (continuing without it): %s", e)

            # 2) Pandas analysis (forced exact faculty filter injection)
            analysis_question = self._inject_faculty_filter(question)

            if self._should_use_pandas(question):
                try:
                    analysis = self.pandas_agent.query(analysis_question)
                except Exception as e:
                    logger.exception("[chatbot] pandas_agent failed: %s", e)
                    analysis = f"(Analysis failed: {e})"

            # 3) Final response
            system = (
                "You are MapAI Assistant. Answer using the survey dataset.\n"
                "If you provide numbers, explain what they mean.\n"
                "If lang='ca', respond in Catalan; otherwise English.\n"
                "Do not invent data.\n"
            )

            user = f"""User question: {question}

Retrieved context (may be empty):
{context}

Data analysis output (may be empty):
{analysis}

Write a clear final answer."""
            msg = self.llm.invoke(
                [{"role": "system", "content": system}, {"role": "user", "content": user}]
            )
            answer_text = getattr(msg, "content", None) or str(msg)

            # 4) If the LLM refuses on a dataset question, force pandas fallback (with faculty injection)
            if self._looks_like_dataset_question(question) and self._looks_like_refusal(answer_text):
                logger.info("[chatbot] Refusal detected; forcing pandas fallback.")
                try:
                    analysis2 = self.pandas_agent.query(analysis_question)
                    user2 = f"""User question: {question}

Data analysis output (authoritative):
{analysis2}

Write a clear final answer."""
                    msg2 = self.llm.invoke(
                        [{"role": "system", "content": system}, {"role": "user", "content": user2}]
                    )
                    answer_text = getattr(msg2, "content", None) or str(msg2)
                except Exception as e:
                    logger.exception("[chatbot] Forced pandas fallback failed: %s", e)

        except Exception as e:
            logger.exception("[chatbot] process_query crashed: %s", e)
            answer_text = "Internal chatbot error while processing your request."

        if not isinstance(answer_text, str) or not answer_text.strip():
            answer_text = analysis.strip() or "I couldn't generate a response."

        return answer_text, sources

    def query(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        lang: str = "en",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        return self.process_query(question, chat_history=chat_history, lang=lang)
