from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from .constants import FACULTY_KEY_COL
from .datastore import STORE
from .normalize import _norm_faculty


def _open_text_joined(question_id: str) -> pd.DataFrame:
    ot = STORE.open_text()
    df_anal = ot.get(question_id)
    if df_anal is None or df_anal.empty:
        return pd.DataFrame()

    surv = STORE.surveys()
    if "row_id" not in surv.columns:
        return df_anal.copy()

    join = df_anal.merge(
        surv[["row_id", "faculty_name", FACULTY_KEY_COL]].copy(),
        on="row_id",
        how="left",
    )
    return join


def open_text_aggregates(question_id: str, faculty: Optional[str]) -> Dict[str, Any]:
    df = _open_text_joined(question_id)
    if df.empty:
        return {"sentiment": {"labels": [], "counts": []}, "topics": {"labels": [], "counts": []}}

    if faculty:
        key = _norm_faculty(faculty)
        if FACULTY_KEY_COL in df.columns:
            df = df[df[FACULTY_KEY_COL] == key]
        else:
            df = df[df.get("faculty_name", pd.Series(dtype=str)).astype(str).str.strip().str.lower() == key]

    if df.empty:
        return {"sentiment": {"labels": [], "counts": []}, "topics": {"labels": [], "counts": []}}

    sent_vc = df.get("sentiment", pd.Series(dtype=str)).value_counts().to_dict()
    sent_order = ["negative", "neutral", "positive"]
    sent_labels = [s for s in sent_order if s in sent_vc]
    sent_counts = [int(sent_vc[s]) for s in sent_labels]

    if "cluster_label" in df.columns and "row_id" in df.columns:
        topic_vc = df.groupby("cluster_label")["row_id"].count().sort_values(ascending=False)
        topic_labels = [str(x) for x in topic_vc.index.tolist()]
        topic_counts = [int(v) for v in topic_vc.values.tolist()]
    else:
        topic_labels, topic_counts = [], []

    return {
        "sentiment": {"labels": sent_labels, "counts": sent_counts},
        "topics": {"labels": topic_labels, "counts": topic_counts},
    }


def open_text_items(question_id: str, faculty: Optional[str]) -> Dict[str, Any]:
    df = _open_text_joined(question_id)
    if df.empty:
        return {"items": []}

    if faculty:
        key = _norm_faculty(faculty)
        if FACULTY_KEY_COL in df.columns:
            df = df[df[FACULTY_KEY_COL] == key]
        else:
            df = df[df.get("faculty_name", pd.Series(dtype=str)).astype(str).str.strip().str.lower() == key]

    if df.empty:
        return {"items": []}

    sort_cols = [c for c in ["cluster_id", "row_id"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols)

    def _safe_int(v: Any, default: int = -1) -> int:
        try:
            if pd.isna(v):
                return default
            return int(v)
        except Exception:
            return default

    def _safe_topics(v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(t).strip() for t in v if str(t).strip()]
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                try:
                    import json

                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(t).strip() for t in arr if str(t).strip()]
                except Exception:
                    pass
            return [p.strip() for p in s.split(",") if p.strip()]
        return []

    items: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        sentiment = str(row.get("sentiment", "neutral") or "neutral").strip().lower()
        if sentiment not in {"negative", "neutral", "positive"}:
            sentiment = "neutral"

        sentiment_fine_raw = str(row.get("sentiment_fine", "") or "").strip()
        sentiment_fine = sentiment_fine_raw if sentiment_fine_raw else sentiment

        items.append(
            {
                "row_id": _safe_int(row.get("row_id", -1), default=-1),
                "sentiment": sentiment,
                "sentiment_fine": sentiment_fine,
                "cluster_id": _safe_int(row.get("cluster_id", -1), default=-1),
                "cluster_label": str(row.get("cluster_label", "") or "").strip() or "Unclassified",
                "main_topics": _safe_topics(row.get("main_topics", [])),
                "english_text": str(row.get("english_text", "") or "").strip(),
            }
        )

    return {"items": items}
