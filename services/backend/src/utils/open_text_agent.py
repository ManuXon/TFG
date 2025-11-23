# src/utils/open_text_agent.py
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import List, Dict, Any, Optional, Literal, TypedDict
import json
from typing import Tuple
import pandas as pd
import os
from src.openai.llm_client import call_llm_json, OPENAI_MODEL

SentimentLabel = Literal["negative", "neutral", "positive"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /app/src
OPEN_TEXT_DIR = os.path.join(BASE_DIR, "data", "open_text")


@dataclass
class OpenTextRowAnalysis:
    row_id: int
    sentiment: SentimentLabel  # coarse, used by current UI
    cluster_id: int
    cluster_label: str
    main_topics: List[str]
    # NEW: finer sentiment, does NOT break UI
    sentiment_fine: str = "neutral"  # e.g. "very_negative", "mixed", etc.


@dataclass
class OpenTextColumnAnalysis:
    question_id: str
    rows: List[OpenTextRowAnalysis]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "row_id": r.row_id,
                    "sentiment": r.sentiment,
                    "cluster_id": r.cluster_id,
                    "cluster_label": r.cluster_label,
                    "main_topics": ",".join(r.main_topics) if r.main_topics else "",
                    # NEW COLUMN: used only if you want later
                    "sentiment_fine": getattr(r, "sentiment_fine", r.sentiment),
                }
                for r in self.rows
            ]
        )


QUESTION_TOPICS: Dict[str, Dict[str, Any]] = {
    "per_ia_oporiscuni_altres": {
        "topics": [
            "Learning enhancement and personalization",
            "Assessment and academic integrity",
            "Cognitive impact and critical thinking",
            "Workload, productivity and automation",
            "Equity, accessibility and inclusion",
            "Ethical, legal and privacy issues",
            "Environmental impact and sustainability",
            "Institutional strategy and university role",
            "Other / unclear",
        ]
    },
    "per_ia_posicprof_perque": {
        "topics": [
            "Inevitability and social/working reality",
            "Need for critical and ethical training",
            "Preserve genuine learning and evaluation",
            "Integrate IA as support tool",
            "Avoid or restrict IA to protect learning",
            "Mixed strategy (integrate + avoid in evaluation)",
            "Institutional constraints and lack of guidance",
            "Personal skepticism or lack of time",
            "Other / unclear",
        ]
    },
    "for_ia_neceformat_altres": {
        "topics": [
            "Basic IA literacy and concepts",
            "Practical tools for teaching",
            "Assessment design and fraud detection",
            "Ethics, law and data protection",
            "Research support and data analysis",
            "Institutional tools and infrastructure",
            "No specific training needs",
            "Other / unclear",
        ]
    },
    "comments": {
        "topics": [
            "Need for institutional policy and guidance",
            "Quality of teaching and evaluation",
            "Environmental and social concerns",
            "Skepticism or strong criticism of IA",
            "Interest in training and participation",
            "Survey design and meta-comments",
            "Positive view: opportunities and change",
            "Other / unclear",
        ]
    },
}

# Finer-grained sentiment labels – you can tweak this later
SENTIMENT_FINE_LABELS = [
    "very_negative",
    "negative",
    "mixed",
    "neutral",
    "positive",
    "very_positive",
]

FINE_TO_COARSE: Dict[str, SentimentLabel] = {
    "very_negative": "negative",
    "negative": "negative",
    "mixed": "neutral",
    "neutral": "neutral",
    "positive": "positive",
    "very_positive": "positive",
}


def load_open_text_analysis() -> Dict[str, pd.DataFrame]:
    """
    Load precomputed analysis for each open-text question.
    Also print debug info so we stop guessing.
    """
    base = OPEN_TEXT_DIR
    os.makedirs(base, exist_ok=True)

    qids = [
        "per_ia_oporiscuni_altres",
        "per_ia_posicprof_perque",
        "for_ia_neceformat_altres",
        "comments",
    ]

    result: Dict[str, pd.DataFrame] = {}

    print(f"[open_text_agent] Loading open-text analysis from {base}")
    for qid in qids:
        path = os.path.join(base, f"{qid}_analysis.parquet")
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                print(f"[open_text_agent]  - {qid}: loaded {len(df)} rows from {path}")
            except Exception as e:
                print(f"[open_text_agent]  - {qid}: FAILED to read {path}: {e}")
                df = pd.DataFrame(
                    columns=[
                        "row_id",
                        "sentiment",
                        "cluster_id",
                        "cluster_label",
                        "main_topics",
                        "sentiment_fine",
                    ]
                )
        else:
            print(f"[open_text_agent]  - {qid}: file NOT FOUND at {path}, using EMPTY df")
            df = pd.DataFrame(
                columns=[
                    "row_id",
                    "sentiment",
                    "cluster_id",
                    "cluster_label",
                    "main_topics",
                    "sentiment_fine",
                ]
            )

        result[qid] = df

    return result

class OpenTextLLMResult(TypedDict):
    sentiment: SentimentLabel
    sentiment_fine: str
    cluster_id: int
    cluster_label: str
    main_topics: list[str]


def call_llm_for_open_text(text: str, question_id: str) -> OpenTextLLMResult:
    system_prompt = """
    You are an assistant that analyses open-text survey answers from university teachers about AI in higher education.

    You MUST return a single JSON object with the following keys:

    - sentiment: one of "negative", "neutral", or "positive"
    - sentiment_fine: a finer sentiment label, examples:
      "very negative", "negative but nuanced", "ambivalent",
      "somewhat positive", "very positive", "mixed", etc.
    - cluster_id: an integer (0–20). Use the same cluster_id for answers
      that talk about similar themes. If unsure, 0 is acceptable.
    - cluster_label: a short (max 6 words) theme label, e.g.
      "cognitive risks", "evaluation redesign", "ethical concerns",
      "integration inevitable", "general training", etc.
    - main_topics: list of 1–5 short topic strings, e.g.
      ["cognitive atrophy", "critical thinking", "evaluation fairness"]

    The JSON MUST NOT contain any other keys and MUST NOT be wrapped in Markdown.
    """

    if question_id == "per_ia_oporiscuni_altres":
        q_description = "Question about opportunities and risks of AI at university."
    elif question_id == "per_ia_posicprof_perque":
        q_description = "Question about the teacher's positioning regarding AI in teaching and assessment."
    elif question_id == "for_ia_neceformat_altres":
        q_description = "Question about training needs related to AI."
    elif question_id == "comments":
        q_description = "General comments about AI and the survey."
    else:
        q_description = "Generic open-text question about AI in higher education."

    user_prompt = f"""
    Question id: {question_id}
    Question type: {q_description}

    Answer (original text, keep language as is):
    \"\"\"{text}\"\"\"

    Analyse this single answer and return the JSON object described above.
    """

    try:
        raw = call_llm_json(system_prompt.strip(), user_prompt.strip(), model=OPENAI_MODEL)
    except Exception:
        # Fail-safe so the pipeline never explodes mid-run
        return OpenTextLLMResult(
            sentiment="neutral",
            sentiment_fine="unknown",
            cluster_id=0,
            cluster_label="Unclassified",
            main_topics=[],
        )

    # --- coercion / validation ---
    sentiment_raw = str(raw.get("sentiment", "neutral")).lower()
    if sentiment_raw not in {"negative", "neutral", "positive"}:
        if re.search(r"(risk|perill|preocupant|very negative)", sentiment_raw):
            sentiment: SentimentLabel = "negative"
        elif re.search(r"(oportunitat|opportunity|very positive)", sentiment_raw):
            sentiment = "positive"
        else:
            sentiment = "neutral"
    else:
        sentiment = sentiment_raw  # type: ignore[assignment]

    sentiment_fine = str(raw.get("sentiment_fine", "") or "").strip() or "unspecified"

    try:
        cluster_id = int(raw.get("cluster_id", 0))
    except (TypeError, ValueError):
        cluster_id = 0

    cluster_label = str(raw.get("cluster_label", "") or "").strip() or "Unclassified"

    topics_raw = raw.get("main_topics", [])
    if isinstance(topics_raw, list):
        main_topics = [str(t).strip() for t in topics_raw if str(t).strip()]
    else:
        main_topics = []

    return OpenTextLLMResult(
        sentiment=sentiment,
        sentiment_fine=sentiment_fine,
        cluster_id=cluster_id,
        cluster_label=cluster_label,
        main_topics=main_topics,
    )