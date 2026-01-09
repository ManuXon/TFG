from __future__ import annotations

import logging
import math
import os
import time
from dataclasses import dataclass
from threading import RLock
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from matplotlib import cm, colors
from wordcloud import WordCloud

from src.utils.data_loader import (
    load_faculties_data,
    load_surveys_data,
    df_to_json_safe,
    PERCEP_PRIORITIES_ORDER,
    percep_priorities_long_en,
    per_students_use_cols,
    per_students_use_axis_short_en,
    per_students_use_axis_long_en,
    per_students_attitudes_cols,
    per_students_attitudes_short_en,
    per_students_attitudes_long_en,
    per_prof_attitude_long_en,
    PER_OPORISCUNI_COLS,
    PER_OPORISCUNI_AXIS_SHORT_EN,
    PER_OPORISCUNI_AXIS_LONG_EN,
    AGREEMENT4_LEVELS,
    TRAINING_RECEIVED_AXIS,
    training_received_long_en,
    TRAINING_INTEREST_MAP,
    TRAINING_INTEREST_ORDER,
    TRAINING_NEEDS_COLS,
    TRAINING_NEEDS_AXIS_SHORT_EN,
    TRAINING_NEEDS_AXIS_LONG_EN,
)
from src.utils.open_text_agent import load_open_text_analysis
from src.utils.tools_normalizer import count_tools

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/api", tags=["Visualizations"])

# =============================================================================
# Constants
# =============================================================================

SCORE_COLS = ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]

LEVELS_ORDER = ["Not at all", "A little", "Quite a bit", "A lot", "Don't know"]
AGREE4_ORDER = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]
PROF_ATT_ORDER = ["Prohibit", "Avoid", "Overcome", "Integrate"]

GENDER_ORDER = ["Female", "Male", "Non-binary", "No answer"]
PROFILE_ORDER = ["Senior Lecturer", "Associate", "PreDoc", "PostDoc", "Collab", "Lecturer", "Professor"]
EXPERIENCE_ORDER = ["Less than 5", "Between 5 and 10", "Between 11 and 20", "More than 20"]
MODE_ORDER = ["In-person", "Online", "Hybrid", "In-person+Online", "In-person+Hybrid", "All modes"]

PER_PROF_ATT_LONG_EN = per_prof_attitude_long_en

KNOW_APP_COLS = [
    "ia_knowledge_text_creation",
    "ia_knowledge_multimedia_creation",
    "ia_knowledge_class_planning",
    "ia_knowledge_material_design",
    "ia_knowledge_activity_design",
    "ia_knowledge_evaluation",
    "ia_knowledge_research_management",
    "ia_knowledge_data_collection",
    "ia_knowledge_transcription_translation",
    "ia_knowledge_data_analysis",
    "ia_knowledge_technical_support",
    "ia_knowledge_ai_experiments",
    "ia_knowledge_inclusion_support",
]

USES_TASK_COLS = [
    "ia_uses_text_creation",
    "ia_uses_multimedia_creation",
    "ia_uses_class_planning",
    "ia_uses_material_design",
    "ia_uses_activity_design",
    "ia_uses_evaluation",
    "ia_uses_research_management",
    "ia_uses_data_collection",
    "ia_uses_transcription_translation",
    "ia_uses_data_analysis",
    "ia_uses_technical_support",
    "ia_uses_ai_experiments",
    "ia_uses_inclusion_support",
]

USES_STUDENT_TASK_COLS = [
    "ia_uses_text_creation_student",
    "ia_uses_multimedia_creation_student",
    "ia_uses_activity_design_student",
    "ia_uses_evaluation_student",
    "ia_uses_research_management_student",
    "ia_uses_data_collection_student",
    "ia_uses_transcription_translation_student",
    "ia_uses_data_analysis_student",
    "ia_uses_technical_support_student",
    "ia_uses_ai_experiments_student",
    "ia_uses_inclusion_support_student",
]

TASK_SHORT_LABELS = {
    "Text": "Text",
    "Media": "Media",
    "Planning": "Planning",
    "Design": "Design",
    "Activity": "Activity",
    "Evaluation": "Evaluation",
    "Research": "Research",
    "Data": "Data",
    "Translation": "Translation",
    "Analysis": "Analysis",
    "Support": "Support",
    "Experiments": "Experiments",
    "Inclusion": "Inclusion",
}

KNOW_NAME_MAP = {
    "ia_knowledge_text_creation": "Text",
    "ia_knowledge_multimedia_creation": "Media",
    "ia_knowledge_class_planning": "Planning",
    "ia_knowledge_material_design": "Design",
    "ia_knowledge_activity_design": "Activity",
    "ia_knowledge_evaluation": "Evaluation",
    "ia_knowledge_research_management": "Research",
    "ia_knowledge_data_collection": "Data",
    "ia_knowledge_transcription_translation": "Translation",
    "ia_knowledge_data_analysis": "Analysis",
    "ia_knowledge_technical_support": "Support",
    "ia_knowledge_ai_experiments": "Experiments",
    "ia_knowledge_inclusion_support": "Inclusion",
}

USES_NAME_MAP = {
    "ia_uses_text_creation": "Text",
    "ia_uses_multimedia_creation": "Media",
    "ia_uses_class_planning": "Planning",
    "ia_uses_material_design": "Design",
    "ia_uses_activity_design": "Activity",
    "ia_uses_evaluation": "Evaluation",
    "ia_uses_research_management": "Research",
    "ia_uses_data_collection": "Data",
    "ia_uses_transcription_translation": "Translation",
    "ia_uses_data_analysis": "Analysis",
    "ia_uses_technical_support": "Support",
    "ia_uses_ai_experiments": "Experiments",
    "ia_uses_inclusion_support": "Inclusion",
}

USES_NICE_NAMES = {
    "ia_uses_text_creation": "Text Creation",
    "ia_uses_multimedia_creation": "Multimedia Creation",
    "ia_uses_class_planning": "Class Planning",
    "ia_uses_material_design": "Material Design",
    "ia_uses_activity_design": "Activity Design",
    "ia_uses_evaluation": "Evaluation",
    "ia_uses_research_management": "Research Management",
    "ia_uses_data_collection": "Data Collection",
    "ia_uses_transcription_translation": "Transcription / Translation",
    "ia_uses_data_analysis": "Data Analysis",
    "ia_uses_technical_support": "Technical Support",
    "ia_uses_ai_experiments": "AI Experiments",
    "ia_uses_inclusion_support": "Inclusion Support",
}

USES_STUDENT_NICE_NAMES = {
    "ia_uses_text_creation_student": "Text Creation",
    "ia_uses_multimedia_creation_student": "Multimedia Creation",
    "ia_uses_activity_design_student": "Activity Design",
    "ia_uses_evaluation_student": "Evaluation",
    "ia_uses_research_management_student": "Research Management",
    "ia_uses_data_collection_student": "Data Collection",
    "ia_uses_transcription_translation_student": "Transcription / Translation",
    "ia_uses_data_analysis_student": "Data Analysis",
    "ia_uses_technical_support_student": "Technical Support",
    "ia_uses_ai_experiments_student": "AI Experiments",
    "ia_uses_inclusion_support_student": "Inclusion Support",
}

KNOW_APP_MAP_1TO4 = {
    "I don't know any": 1.0,
    "I know a few": 2.0,
    "I know several": 3.0,
    "I know many": 4.0,
}

USES_FREQ_MAP_1TO4 = {
    "Never": 1.0,
    "Sometimes": 2.0,
    "Often": 3.0,
    "Very often": 4.0,
}

# =============================================================================
# Normalization + small utilities
# =============================================================================

_FACULTY_KEY_COL = "_faculty_key"
DATA_TTL_SEC = int(os.getenv("DATA_TTL_SEC", "0"))  # 0 = never reload


def _norm_opt(x: Optional[str]) -> str:
    return (x or "").strip()


def _norm_faculty(x: Optional[str]) -> str:
    return _norm_opt(x).lower()


def _norm_demo(x: Optional[str]) -> str:
    v = _norm_opt(x)
    return "" if v in {"", "All"} else v


def _sanitize_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        if not math.isfinite(f):
            return None
        return f
    except Exception:
        return None


def _color_rgb_to_list(v: Any) -> Optional[List[int]]:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (list, tuple)) and len(v) == 3:
        try:
            return [int(x) for x in v]
        except Exception:
            return None
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                import json
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) == 3:
                    return [int(x) for x in arr]
            except Exception:
                return None
    return None


def _counts_for_column(df: pd.DataFrame, col: str, order: Optional[List[str]] = None) -> Dict[str, Any]:
    if col not in df.columns:
        return {"categories": [], "counts": []}
    vc = df[col].dropna().astype(str).value_counts().to_dict()
    if order:
        cats = [c for c in order if vc.get(c, 0) > 0]
        cnts = [int(vc[c]) for c in cats]
    else:
        items = sorted(vc.items(), key=lambda x: (-x[1], x[0]))
        cats = [k for k, _ in items]
        cnts = [int(v) for _, v in items]
    return {"categories": cats, "counts": cnts}


def _age_counts(df: pd.DataFrame) -> Dict[str, Any]:
    if "age" not in df.columns:
        return {"categories": [], "counts": []}
    ages = pd.to_numeric(df["age"], errors="coerce")
    bins = [-np.inf, 20, 30, 40, 50, 60, 70, np.inf]
    labels = ["<20", "20s", "30s", "40s", "50s", "60s", "70+"]
    cut = pd.cut(ages, bins=bins, labels=labels, right=False, include_lowest=True, duplicates="drop")
    vc = cut.value_counts().to_dict()
    wanted = ["20s", "30s", "40s", "50s", "60s", "70+"]
    cats = [lbl for lbl in wanted if int(vc.get(lbl, 0)) > 0]
    cnts = [int(vc.get(lbl, 0)) for lbl in cats]
    return {"categories": cats, "counts": cnts}


def truncate_colormap(cmap_name: str, minval: float = 0.4, maxval: float = 1.0, n: int = 256):
    base = cm.get_cmap(cmap_name)
    new_colors = base(np.linspace(minval, maxval, n))
    return colors.LinearSegmentedColormap.from_list(f"{cmap_name}_trunc_{minval}_{maxval}", new_colors)


purples_trunc = truncate_colormap("Purples", minval=0.4, maxval=1.0)
reds_trunc = truncate_colormap("Reds", minval=0.4, maxval=1.0)


def _empty_svg(message: str) -> str:
    return (
        "<svg style='max-width:100%;height:280px' viewBox='0 0 1000 280' "
        "xmlns='http://www.w3.org/2000/svg'>"
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
        f"fill='#6b21a8' font-size='20'>{message}</text>"
        "</svg>"
    )


def _sanitize_num_list(seq: List[Any]) -> List[Any]:
    out: List[Any] = []
    for x in seq:
        if isinstance(x, (np.integer,)):
            x = int(x)
        elif isinstance(x, (np.floating,)):
            x = float(x)
        if isinstance(x, float) and not math.isfinite(x):
            x = 0.0
        out.append(x)
    return out


# =============================================================================
# Data store (single-load per worker, optional TTL)
# =============================================================================

@dataclass(frozen=True)
class _Meta:
    faculty_name: Optional[str]
    latitude: Any
    longitude: Any
    color: Any
    short_name: Any
    color_rgb: Optional[List[int]]


class DataStore:
    """
    Loads + preprocesses data once per process (gunicorn/uvicorn worker).
    - Adds a normalized faculty key column to surveys + faculties.
    - Converts common dims to category dtype for lower RAM + faster groupby.
    - Converts SCORE_COLS to numeric once.
    - Normalizes faculties.color_rgb to list[int] once.
    """

    def __init__(self):
        self._lock = RLock()
        self._loaded_at: float = 0.0
        self._surveys: pd.DataFrame = pd.DataFrame()
        self._faculties: pd.DataFrame = pd.DataFrame()
        self._open_text: Dict[str, pd.DataFrame] = {}
        self._meta_by_key: Dict[str, _Meta] = {}

    def _expired(self) -> bool:
        return DATA_TTL_SEC > 0 and self._loaded_at and (time.time() - self._loaded_at) > DATA_TTL_SEC

    def _load_if_needed(self) -> None:
        with self._lock:
            if self._loaded_at and not self._expired():
                return

            surv = load_surveys_data()
            if not isinstance(surv, pd.DataFrame):
                raise RuntimeError("load_surveys_data() did not return a DataFrame")

            fac = load_faculties_data()
            if not isinstance(fac, pd.DataFrame):
                fac = pd.DataFrame(columns=["faculty_name"])

            ot = load_open_text_analysis()
            ot = ot if isinstance(ot, dict) else {}

            surv = self._prep_surveys(surv)
            fac, meta = self._prep_faculties(fac)

            self._surveys = surv
            self._faculties = fac
            self._open_text = ot
            self._meta_by_key = meta
            self._loaded_at = time.time()

    def surveys(self) -> pd.DataFrame:
        self._load_if_needed()
        return self._surveys

    def faculties(self) -> pd.DataFrame:
        self._load_if_needed()
        return self._faculties

    def open_text(self) -> Dict[str, pd.DataFrame]:
        self._load_if_needed()
        return self._open_text

    def meta_by_key(self) -> Dict[str, _Meta]:
        self._load_if_needed()
        return self._meta_by_key

    @staticmethod
    def _prep_surveys(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        if "faculty_name" in out.columns:
            out[_FACULTY_KEY_COL] = out["faculty_name"].astype(str).str.strip().str.lower()
        else:
            out[_FACULTY_KEY_COL] = ""

        # category dtypes help memory + groupby perf
        for c in ["faculty_name", "gender", "teaching_experience", "ub_profile", "teaching_mode"]:
            if c in out.columns:
                try:
                    out[c] = out[c].astype("category")
                except Exception:
                    pass

        # scores numeric once
        for c in SCORE_COLS:
            if c in out.columns:
                out[c] = pd.to_numeric(out[c], errors="coerce")

        return out

    @staticmethod
    def _prep_faculties(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, _Meta]]:
        out = df.copy()

        if "faculty_name" in out.columns:
            out[_FACULTY_KEY_COL] = out["faculty_name"].astype(str).str.strip().str.lower()
        else:
            out[_FACULTY_KEY_COL] = ""

        for col in ["latitude", "longitude", "color", "short_name", "color_rgb"]:
            if col not in out.columns:
                out[col] = pd.NA

        out["color_rgb"] = out["color_rgb"].apply(_color_rgb_to_list)

        meta: Dict[str, _Meta] = {}
        for _, r in out.iterrows():
            k = str(r.get(_FACULTY_KEY_COL, "") or "")
            if not k:
                continue
            meta[k] = _Meta(
                faculty_name=r.get("faculty_name", None),
                latitude=r.get("latitude", None),
                longitude=r.get("longitude", None),
                color=r.get("color", None),
                short_name=r.get("short_name", None),
                color_rgb=r.get("color_rgb", None),
            )

        return out[
            ["faculty_name", _FACULTY_KEY_COL, "latitude", "longitude", "color", "short_name", "color_rgb"]], meta


STORE = DataStore()


# =============================================================================
# Filtering helpers (views vs copies)
# =============================================================================

def _df_faculty(df: pd.DataFrame, faculty: Optional[str]) -> pd.DataFrame:
    if not faculty:
        return df
    key = _norm_faculty(faculty)
    if _FACULTY_KEY_COL in df.columns:
        return df[df[_FACULTY_KEY_COL] == key]
    # fallback if someone passes a df without preproc
    if "faculty_name" not in df.columns:
        return df.iloc[0:0]
    return df[df["faculty_name"].astype(str).str.strip().str.lower() == key]


def _apply_demo_filters(df: pd.DataFrame, gender: Optional[str], experience: Optional[str],
                        profile: Optional[str]) -> pd.DataFrame:
    x = df
    g = _norm_demo(gender)
    e = _norm_demo(experience)
    p = _norm_demo(profile)
    if g and "gender" in x.columns:
        x = x[x["gender"] == g]
    if e and "teaching_experience" in x.columns:
        x = x[x["teaching_experience"] == e]
    if p and "ub_profile" in x.columns:
        x = x[x["ub_profile"] == p]
    return x


def _filtered_view(faculty: Optional[str], gender: Optional[str], experience: Optional[str],
                   profile: Optional[str]) -> pd.DataFrame:
    base = STORE.surveys()
    x = _df_faculty(base, faculty)
    x = _apply_demo_filters(x, gender, experience, profile)
    return x


def _filtered_copy(
        faculty: Optional[str],
        gender: Optional[str],
        experience: Optional[str],
        profile: Optional[str],
        cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    x = _filtered_view(faculty, gender, experience, profile)
    if cols:
        cols2 = [c for c in cols if c in x.columns]
        return x.loc[:, cols2].copy()
    return x.copy()


def _faculty_meta_by_name() -> pd.DataFrame:
    # already preprocessed + has _faculty_key
    fdf = STORE.faculties()
    if fdf.empty:
        return pd.DataFrame(
            columns=["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb", _FACULTY_KEY_COL])
    return fdf.copy()


# =============================================================================
# Wordcloud caching
# =============================================================================

def _cache_key(faculty: str, gender: Optional[str], experience: Optional[str], profile: Optional[str]) -> Tuple[
    str, str, str, str]:
    return (_norm_faculty(faculty), _norm_demo(gender), _norm_demo(experience), _norm_demo(profile))


def _finalize_wc_svg(svg: str) -> str:
    svg = svg.replace("<svg ", "<svg style='max-width:100%;height:auto;display:block' ")
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s}"
        "text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}"
        "</style></svg>",
    )
    return svg


@lru_cache(maxsize=512)
def _cached_knowledge_wordcloud_svg(key: Tuple[str, str, str, str]) -> str:
    faculty_key, gender, exp, prof = key
    df = _filtered_copy(faculty_key, gender, exp, prof, cols=list(KNOW_NAME_MAP.keys()))
    if df.empty:
        return _empty_svg("No data for the selected filters.")

    missing = [c for c in KNOW_NAME_MAP.keys() if c not in df.columns]
    if missing:
        return _empty_svg("No data available (missing columns).")

    # map to numeric only in this local copy
    for col in KNOW_NAME_MAP.keys():
        df[col] = df[col].map(KNOW_APP_MAP_1TO4).fillna(0.0)

    total_scores = df[list(KNOW_NAME_MAP.keys())].sum().to_dict()
    gamma = 1.25
    freqs = {KNOW_NAME_MAP[c]: float(v) ** gamma for c, v in total_scores.items()}

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=50,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=reds_trunc,
    ).generate_from_frequencies(freqs)

    return _finalize_wc_svg(wc.to_svg(embed_font=True))


@lru_cache(maxsize=512)
def _cached_uses_wordcloud_svg(key: Tuple[str, str, str, str]) -> str:
    faculty_key, gender, exp, prof = key
    df = _filtered_copy(faculty_key, gender, exp, prof, cols=list(USES_NAME_MAP.keys()))
    if df.empty:
        return _empty_svg("No data for the selected filters.")

    missing = [c for c in USES_NAME_MAP.keys() if c not in df.columns]
    if missing:
        return _empty_svg("No data available (missing columns).")

    for col in USES_NAME_MAP.keys():
        df[col] = df[col].map(USES_FREQ_MAP_1TO4).fillna(0.0)

    total_scores = df[list(USES_NAME_MAP.keys())].sum().to_dict()
    gamma = 1.25
    freqs = {USES_NAME_MAP[c]: float(v) ** gamma for c, v in total_scores.items()}

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=50,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=purples_trunc,
    ).generate_from_frequencies(freqs)

    return _finalize_wc_svg(wc.to_svg(embed_font=True))


@lru_cache(maxsize=512)
def _cached_tools_wordcloud_svg(key: Tuple[str, str, str, str]) -> str:
    faculty_key, gender, exp, prof = key
    df = _filtered_view(faculty_key, gender, exp, prof)
    freq_df = count_tools(df, source_col="ia_uses_tools", unique_per_respondent=True)
    if freq_df.empty:
        return _empty_svg("No data for the selected filters.")

    counts = dict(zip(freq_df["tool"], freq_df["count"]))
    vals = np.array(list(counts.values()), dtype=float)
    vmin, vmax = float(vals.min()), float(vals.max())

    gamma = 2.5
    floor = 0.22
    cap = 130

    if vmax == vmin:
        weights = {k: 1.0 for k in counts}
    else:
        weights = {}
        for k, v in counts.items():
            z = (float(v) - vmin) / (vmax - vmin)
            w = floor + (1.0 - floor) * (z ** gamma)
            weights[k] = float(w)

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=80,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=purples_trunc,
        min_font_size=10,
        max_font_size=cap,
        font_step=1,
        random_state=41,
    ).generate_from_frequencies(weights)

    return _finalize_wc_svg(wc.to_svg(embed_font=True))


# =============================================================================
# Open text helpers
# =============================================================================

def _open_text_joined(question_id: str) -> pd.DataFrame:
    ot = STORE.open_text()
    df_anal = ot.get(question_id)
    if df_anal is None or df_anal.empty:
        return pd.DataFrame()

    surv = STORE.surveys()
    if "row_id" not in surv.columns:
        return df_anal.copy()

    join = df_anal.merge(surv[["row_id", "faculty_name", _FACULTY_KEY_COL]].copy(), on="row_id", how="left")
    return join


def _open_text_aggregates(question_id: str, faculty: Optional[str]) -> Dict[str, Any]:
    df = _open_text_joined(question_id)
    if df.empty:
        return {"sentiment": {"labels": [], "counts": []}, "topics": {"labels": [], "counts": []}}

    if faculty:
        key = _norm_faculty(faculty)
        if _FACULTY_KEY_COL in df.columns:
            df = df[df[_FACULTY_KEY_COL] == key]
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

    return {"sentiment": {"labels": sent_labels, "counts": sent_counts},
            "topics": {"labels": topic_labels, "counts": topic_counts}}


def _open_text_items(question_id: str, faculty: Optional[str]) -> Dict[str, Any]:
    df = _open_text_joined(question_id)
    if df.empty:
        return {"items": []}

    if faculty:
        key = _norm_faculty(faculty)
        if _FACULTY_KEY_COL in df.columns:
            df = df[df[_FACULTY_KEY_COL] == key]
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


# =============================================================================
# Survey summary / distribution
# =============================================================================

@router.get("/survey/summary")
def survey_summary(
        faculty: Optional[str] = Query(None, description="Optional faculty name (short EN) to filter responses"),
) -> Dict[str, Any]:
    df = _df_faculty(STORE.surveys(), faculty)
    total_responses = int(len(df))
    total_faculties = int(STORE.surveys().get("faculty_name", pd.Series(dtype=str)).nunique())
    return {"total_responses": total_responses, "total_faculties": total_faculties}


@router.get("/survey/distribution")
def survey_distribution(
        category: Literal["age", "gender", "profile", "experience", "mode"] = Query(..., description="Which dimension"),
        faculty: Optional[str] = Query(None, description="Optional faculty filter"),
) -> Dict[str, Any]:
    base = _df_faculty(STORE.surveys(), faculty)
    if base.empty:
        return {"categories": [], "counts": []}

    if category == "age":
        return _age_counts(base)
    if category == "gender":
        return _counts_for_column(base, "gender", GENDER_ORDER)
    if category == "profile":
        return _counts_for_column(base, "ub_profile", PROFILE_ORDER)
    if category == "experience":
        return _counts_for_column(base, "teaching_experience", EXPERIENCE_ORDER)
    if category == "mode":
        return _counts_for_column(base, "teaching_mode", MODE_ORDER)

    raise HTTPException(status_code=400, detail="Unknown category")


@router.get("/survey/faculties")
def survey_faculties(min_count: int = 1) -> Dict[str, Any]:
    df = STORE.surveys()
    if df.empty or "faculty_name" not in df.columns:
        return {"faculties": [], "total": 0}

    vc = df["faculty_name"].dropna().astype(str).value_counts().sort_index()
    rows = [{"faculty_name": name, "responses": int(count)} for name, count in vc.items() if
            int(count) >= int(min_count)]
    return {"faculties": rows, "total": int(sum(r["responses"] for r in rows))}


# =============================================================================
# Faculty scores / treemap / spike-map
# =============================================================================

@router.get("/faculty/{faculty_name}/scores")
def faculty_scores(
        faculty_name: str,
        gender: Optional[str] = None,
        teaching_experience: Optional[str] = None,
        ub_profile: Optional[str] = None,
) -> Dict[str, Any]:
    key = _norm_faculty(faculty_name)

    x = _filtered_view(key, gender, teaching_experience, ub_profile)
    if x.empty:
        raise HTTPException(status_code=404, detail=f"Faculty '{faculty_name}' not found")

    # copy only needed columns (we assign row_mean)
    cols = ["faculty_name", *SCORE_COLS]
    if "color" in x.columns:
        cols.append("color")
    fdf = x.loc[:, [c for c in cols if c in x.columns]].copy()

    fdf["row_mean"] = fdf[SCORE_COLS].mean(axis=1, skipna=True)
    total_score = float(fdf["row_mean"].mean(skipna=True) or 0.0)

    metric_means = fdf[SCORE_COLS].mean(numeric_only=True, skipna=True).to_dict()
    metric_means = {k: (_sanitize_float(v) or 0.0) for k, v in metric_means.items()}

    meta = STORE.meta_by_key().get(key)
    color = None
    if meta and meta.color is not None and not (isinstance(meta.color, float) and math.isnan(meta.color)):
        color = meta.color
    elif "color" in fdf.columns and not fdf["color"].dropna().empty:
        color = fdf["color"].dropna().iloc[0]

    return {
        "faculty_name": str(fdf["faculty_name"].iloc[0]),
        "color": color,
        **metric_means,
        "total_score": float(total_score),
    }


@router.get("/treemap-data")
def get_treemap_data(
    gender: Optional[str] = None,
    teaching_experience: Optional[str] = None,
    ub_profile: Optional[str] = None,
):
    df = _filtered_view(None, gender, teaching_experience, ub_profile)
    if df.empty:
        return []

    # Group means for the 4 score columns
    fac_means = (
        df.groupby("faculty_name", observed=True)[SCORE_COLS]
        .mean(numeric_only=True)
        .reset_index()
    )

    # IMPORTANT: only sanitize + fill numeric columns (faculty_name may be Categorical)
    num_cols = [c for c in SCORE_COLS if c in fac_means.columns]
    if not num_cols:
        return []

    fac_means[num_cols] = (
        fac_means[num_cols]
        .replace([np.inf, -np.inf], np.nan)
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )

    fac_means["overall_faculty_score"] = fac_means[num_cols].mean(axis=1).fillna(0.0)

    meta = _faculty_meta_by_name()
    fac_means = fac_means.merge(
        meta[["faculty_name", "color", "short_name", "color_rgb"]],
        on="faculty_name",
        how="left",
    )

    rows: List[Dict[str, Any]] = []
    for _, row in fac_means.iterrows():
        k = float(row.get("knowledge_score", 0.0) or 0.0)
        u = float(row.get("uses_score", 0.0) or 0.0)
        p = float(row.get("perceptions_score", 0.0) or 0.0)
        t = float(row.get("training_needs_score", 0.0) or 0.0)

        # skip full-missing faculties (all 0 after fill)
        if k == 0.0 and u == 0.0 and p == 0.0 and t == 0.0:
            continue

        overall_val = float(row.get("overall_faculty_score", 0.0) or 0.0)
        if not np.isfinite(overall_val):
            overall_val = 0.0

        short_name = row.get("short_name", None)
        color_rgb = row.get("color_rgb", None)

        for dim_label, dim_val in [("Knowledge", k), ("Uses", u), ("Perceptions", p), ("Training", t)]:
            if not np.isfinite(dim_val):
                dim_val = 0.0
            rows.append(
                {
                    "faculty_name": str(row["faculty_name"]),
                    "label": dim_label,
                    "value": float(dim_val),
                    "overall_faculty_score": float(overall_val),
                    "short_name": str(short_name) if short_name is not None else str(row["faculty_name"]),
                    "color": row.get("color", None),
                    "color_rgb": color_rgb if color_rgb is not None else None,
                }
            )

    if not rows:
        return []

    out_df = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan)
    out_df = out_df.where(pd.notna(out_df), None)
    return df_to_json_safe(out_df)

@router.get("/spike-map")
def get_spike_map_data(
        category: str = "All",
        gender: Optional[str] = None,
        teaching_experience: Optional[str] = None,
        ub_profile: Optional[str] = None,
):
    """
    Aggregates by faculty_name, attaches faculty metadata, avoids full-data copies.
    """
    try:
        df = _filtered_view(None, gender, teaching_experience, ub_profile)
        if df.empty or "faculty_name" not in df.columns:
            return df_to_json_safe(
                pd.DataFrame(
                    columns=[
                        "faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb",
                        "category_score", "knowledge_score", "uses_score", "perceptions_score", "training_needs_score",
                        "n_responses"
                    ]
                )
            )

        if category == "All":
            category_score = df[SCORE_COLS].mean(axis=1, skipna=True)
        else:
            col = {
                "knowledge": "knowledge_score",
                "uses": "uses_score",
                "perceptions": "perceptions_score",
                "training": "training_needs_score",
            }.get(category, "knowledge_score")
            category_score = df[col] if col in df.columns else 0.0

        tmp = df.loc[:, ["faculty_name", *[c for c in SCORE_COLS if c in df.columns]]].copy()
        tmp["category_score"] = category_score

        agg = (
            tmp.groupby("faculty_name", dropna=False, observed=True)
            .agg(
                category_score=("category_score", "mean"),
                knowledge_score=("knowledge_score", "mean"),
                uses_score=("uses_score", "mean"),
                perceptions_score=("perceptions_score", "mean"),
                training_needs_score=("training_needs_score", "mean"),
                n_responses=("faculty_name", "size"),
            )
            .reset_index()
        )

        meta = _faculty_meta_by_name()
        out = agg.merge(meta[["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb"]],
                        on="faculty_name", how="left")

        out = out.replace([np.inf, -np.inf], np.nan)
        out = out.where(pd.notna(out), None)
        return df_to_json_safe(out)

    except Exception as e:
        logger.exception("Error computing spike-map")
        raise HTTPException(status_code=500, detail=f"Failed to compute spike-map: {type(e).__name__}")


# =============================================================================
# Knowledge distribution + correlation + wordcloud
# =============================================================================

@router.get("/faculty/{faculty_name}/knowledge-distribution")
def knowledge_distribution(
    faculty_name: str,
    demographic1: str = "gender",
    demographic2: Optional[str] = None,
):
    df = _df_faculty(STORE.surveys(), faculty_name).copy()

    knowledge_map = {"No knowledge": 1, "Little knowledge": 2, "Good knowledge": 3, "Expert knowledge": 4}
    if "ia_knowledge" not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    # ensure numeric
    df["knowledge_num"] = pd.to_numeric(df["ia_knowledge"].map(knowledge_map), errors="coerce")

    col_map = {"gender": "gender", "experience": "teaching_experience", "profile": "ub_profile"}
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    if col1 not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    # SINGLE DEMO
    if not col2:
        grouped = (
            df.groupby(col1, observed=True)["knowledge_num"]
            .mean()
            .reset_index()
            .rename(columns={col1: "category", "knowledge_num": "average_score"})
        )
        grouped["average_score"] = pd.to_numeric(grouped["average_score"], errors="coerce").fillna(0.0).round(3)
        return {
            "mode": "single",
            "demographics": [demographic1],
            "categories": grouped["category"].astype(str).tolist(),
            "values": grouped["average_score"].tolist(),
        }

    # DUAL DEMO
    if col2 not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    g = (
        df.groupby([col1, col2], observed=True)["knowledge_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    g["n_main"] = g.groupby("main", observed=True)["n_sub"].transform("sum")

    main_avg_map = df.groupby(col1, observed=True)["knowledge_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # protect division by zero
    g["contribution"] = np.where(
        g["n_main"].astype(float) > 0,
        (g["mean_sub"].astype(float) * g["n_sub"].astype(float)) / g["n_main"].astype(float),
        0.0,
    )

    # DO NOT fillna on the whole dataframe. Only numeric cols.
    num_cols = ["mean_sub", "n_sub", "n_main", "main_avg", "contribution"]
    g[num_cols] = (
        g[num_cols]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]].to_dict(orient="records"),
    }



@router.get("/faculty/{faculty_name}/knowledge-functionality-correlation")
def get_knowledge_functionality_correlation(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    # copy only what we mutate
    needed = ["ia_knowledge", *KNOW_APP_COLS]
    df = _filtered_copy(faculty_name, gender, experience, profile, cols=needed)
    if df.empty:
        return []

    missing = [c for c in KNOW_APP_COLS if c not in df.columns]
    if missing or "ia_knowledge" not in df.columns:
        return []

    for col in KNOW_APP_COLS:
        df[col] = df[col].map(KNOW_APP_MAP_1TO4)

    df = df.dropna(subset=["ia_knowledge"])
    if df.empty:
        return []

    total_n = len(df)
    grouped_means = df.groupby("ia_knowledge", observed=True)[KNOW_APP_COLS].mean()
    group_counts = df.groupby("ia_knowledge", observed=True).size()

    group_mean = grouped_means.mean(axis=1)
    group_min = grouped_means.min(axis=1)
    group_max = grouped_means.max(axis=1)
    group_pct = (group_counts / float(total_n)) * 100.0 if total_n > 0 else 0.0

    result_df = grouped_means.copy()
    result_df["n"] = group_counts.astype(int)
    result_df["pct"] = group_pct
    result_df["group_mean"] = group_mean
    result_df["group_min"] = group_min
    result_df["group_max"] = group_max

    result_df = result_df.reset_index().rename(columns={"ia_knowledge": "knowledge_label"})
    numeric_cols = KNOW_APP_COLS + ["n", "pct", "group_mean", "group_min", "group_max"]
    result_df[numeric_cols] = result_df[numeric_cols].replace([math.inf, -math.inf], 0).fillna(0)

    return result_df.to_dict(orient="records")


@router.get("/faculty/{faculty_name}/knowledge-applications-wordcloud-svg")
def knowledge_applications_wordcloud_svg(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    svg = _cached_knowledge_wordcloud_svg(_cache_key(faculty_name, gender, experience, profile))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/knowledge-applications-distribution-count")
def knowledge_applications_distribution_count(
        faculty_name: str,
        app_label: str = Query(..., description="Label: Text/Media/Planning/..."),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)
    if df.empty:
        return {"label": app_label, "levels": list(KNOW_APP_MAP_1TO4.keys()), "counts": {}, "total": 0}

    reverse_map = {v: k for k, v in KNOW_NAME_MAP.items()}
    col = reverse_map.get(app_label)
    if not col:
        raise HTTPException(status_code=400, detail=f"Unknown app_label '{app_label}'")
    if col not in df.columns:
        return {"label": app_label, "levels": list(KNOW_APP_MAP_1TO4.keys()), "counts": {}, "total": 0}

    levels = ["I don't know any", "I know a few", "I know several", "I know many"]
    counts = {lvl: int((df[col] == lvl).sum()) for lvl in levels}
    total = int(sum(counts.values()))
    return {"label": app_label, "levels": levels, "counts": counts, "total": total}


# =============================================================================
# Sankey (vectorized subgroup->faculty + reduced Python loops)
# =============================================================================

def get_sankey_chart_data() -> Dict[str, Any]:
    df = STORE.surveys()

    # pick only columns we need
    needed = ["faculty_name", "gender", "teaching_experience", "ub_profile",
              *[c for c in SCORE_COLS if c in df.columns]]
    work = df.loc[:, [c for c in needed if c in df.columns]].copy()
    fmeta = _faculty_meta_by_name()

    # sanitize categoricals without mutating base
    if "gender" in work.columns:
        work["gender"] = work["gender"].astype(str).where(work["gender"].notna(), "No answer")

    for c in ["teaching_experience", "ub_profile"]:
        if c in work.columns:
            work[c] = work[c].where(pd.notna(work[c]), None)

    genders = [v for v in work.get("gender", pd.Series(dtype=str)).dropna().unique().tolist() if str(v).strip()]
    exps = [v for v in work.get("teaching_experience", pd.Series(dtype=str)).dropna().unique().tolist() if
            str(v).strip()]
    profiles = [v for v in work.get("ub_profile", pd.Series(dtype=str)).dropna().unique().tolist() if str(v).strip()]

    faculties_list = fmeta.get("faculty_name", pd.Series(dtype=str)).astype(str).tolist()

    labels = (
            ["Knowledge", "Uses", "Perceptions", "Training Needs"]
            + ["Gender", "Teaching Experience", "UB Profile"]
            + list(map(str, genders))
            + list(map(str, exps))
            + list(map(str, profiles))
            + faculties_list
    )
    label_to_idx = {str(lbl): i for i, lbl in enumerate(labels)}

    first_layer_indices = {"knowledge_score": 0, "uses_score": 1, "perceptions_score": 2, "training_needs_score": 3}
    second_layer_indices = {"gender": 4, "teaching_experience": 5, "ub_profile": 6}

    # subgroup nodes (strings) across all three demographic dimensions
    third_layer_indices = {}
    for v in list(map(str, genders)) + list(map(str, exps)) + list(map(str, profiles)):
        if v in label_to_idx:
            third_layer_indices[v] = label_to_idx[v]

    faculty_indices = {str(f): label_to_idx[str(f)] for f in faculties_list if str(f) in label_to_idx}

    sources: List[int] = []
    targets: List[int] = []
    values: List[float] = []

    # ---------------------------
    # score dimension -> demographic block
    # (keep same semantics as your original code, but compute totals efficiently)
    # ---------------------------
    for score in ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]:
        if score not in work.columns:
            continue
        score_total = float(pd.to_numeric(work[score], errors="coerce").sum(skipna=True) or 0.0)
        for category, cat_idx in second_layer_indices.items():
            if category not in work.columns:
                continue
            sources.append(first_layer_indices[score])
            targets.append(cat_idx)
            values.append(score_total)

    # ---------------------------
    # demographic block -> subgroup (vectorized groupby)
    # value = sum of all score columns for that subgroup
    # ---------------------------
    score_present = [c for c in SCORE_COLS if c in work.columns]
    if score_present:
        for category, cat_idx in second_layer_indices.items():
            if category not in work.columns:
                continue

            g = (
                work.groupby(category, observed=True)[score_present]
                .sum(numeric_only=True, min_count=1)
            )
            if g.empty:
                continue
            subgroup_vals = g.sum(axis=1, skipna=True)

            for subgroup_value, v in subgroup_vals.items():
                if pd.isna(subgroup_value):
                    continue
                sv = str(subgroup_value)
                idx = third_layer_indices.get(sv)
                if idx is None:
                    continue
                sources.append(cat_idx)
                targets.append(idx)
                values.append(float(v) if pd.notna(v) else 0.0)

    # ---------------------------
    # subgroup -> faculty (vectorized + aggregated)
    # This replaces iterrows() and avoids emitting one edge per row.
    # ---------------------------
    if score_present and "faculty_name" in work.columns:
        faculty_score = work[score_present].sum(axis=1, skipna=True)

        long = work[["faculty_name", "gender", "teaching_experience", "ub_profile"]].copy()
        long["faculty_score"] = faculty_score
        long = long.melt(
            id_vars=["faculty_name", "faculty_score"],
            value_vars=["gender", "teaching_experience", "ub_profile"],
            var_name="category",
            value_name="subgroup",
        ).dropna(subset=["faculty_name", "subgroup"])

        flows = (
            long.groupby(["subgroup", "faculty_name"], observed=True)["faculty_score"]
            .sum(min_count=1)
            .reset_index()
        )

        for _, r in flows.iterrows():
            subgroup = str(r["subgroup"])
            fac = str(r["faculty_name"])
            if subgroup not in third_layer_indices:
                continue
            if fac not in faculty_indices:
                continue
            sources.append(third_layer_indices[subgroup])
            targets.append(faculty_indices[fac])
            v = r["faculty_score"]
            values.append(float(v) if pd.notna(v) else 0.0)

    # Faculty colors
    faculty_colors: Dict[str, str] = {}
    if "color" in fmeta.columns:
        for _, r in fmeta.iterrows():
            fac = str(r.get("faculty_name", ""))
            col = r.get("color", None)
            faculty_colors[fac] = (
                str(col)
                if col is not None and not (isinstance(col, float) and math.isnan(col))
                else "#999999"
            )

    return {
        "sources": _sanitize_num_list(sources),
        "targets": _sanitize_num_list(targets),
        "values": _sanitize_num_list(values),
        "labels": [str(x) for x in labels],
        "faculty_colors": {str(k): str(v) for k, v in faculty_colors.items()},
    }


@router.get("/sankey-data")
def sankey_data():
    return get_sankey_chart_data()


# =============================================================================
# Normative / Uses / Tools / Perceptions / Training / Open-text
# =============================================================================

@router.get("/faculty/{faculty_name}/normative-distribution")
def get_normative_distribution(faculty_name: str):
    df = _df_faculty(STORE.surveys(), faculty_name)
    column = "ia_normative_ub"
    if column not in df.columns:
        return {"categories": [], "values": []}
    distribution = df[column].value_counts().to_dict()
    return {"categories": list(distribution.keys()), "values": list(distribution.values())}


@router.get("/faculty/{faculty_name}/uses-distribution")
def uses_distribution(
    faculty_name: str,
    demographic1: str = "gender",
    demographic2: Optional[str] = None,
):
    df = _df_faculty(STORE.surveys(), faculty_name).copy()

    uses_map = {"No use": 1, "Low use": 2, "Moderate use": 3, "Advanced use": 4}
    if "ia_uses" not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    df["uses_num"] = pd.to_numeric(df["ia_uses"].map(uses_map), errors="coerce")

    col_map = {"gender": "gender", "experience": "teaching_experience", "profile": "ub_profile"}
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    if col1 not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    # SINGLE DEMO
    if not col2:
        grouped = (
            df.groupby(col1, observed=True)["uses_num"]
            .mean()
            .reset_index()
            .rename(columns={col1: "category", "uses_num": "average_score"})
        )
        grouped["average_score"] = pd.to_numeric(grouped["average_score"], errors="coerce").fillna(0.0).round(3)
        return {
            "mode": "single",
            "demographics": [demographic1],
            "categories": grouped["category"].astype(str).tolist(),
            "values": grouped["average_score"].tolist(),
        }

    # DUAL DEMO
    if col2 not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    g = (
        df.groupby([col1, col2], observed=True)["uses_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    # n_main per main group
    g["n_main"] = g.groupby("main", observed=True)["n_sub"].transform("sum")

    # main_avg from original df
    main_avg_map = df.groupby(col1, observed=True)["uses_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # contribution (protect division by zero)
    g["contribution"] = np.where(
        g["n_main"].astype(float) > 0,
        (g["mean_sub"].astype(float) * g["n_sub"].astype(float)) / g["n_main"].astype(float),
        0.0,
    )

    # ONLY fill numeric cols (never touch 'main'/'sub' categoricals)
    num_cols = ["mean_sub", "n_sub", "n_main", "main_avg", "contribution"]
    g[num_cols] = g[num_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]].to_dict(orient="records"),
    }



@router.get("/faculty/{faculty_name}/proposes-distribution")
def get_proposes_distribution(faculty_name: str):
    df = _df_faculty(STORE.surveys(), faculty_name)
    column = "ia_proposes_students"
    order = ["Never", "Sometimes", "Often", "Very often"]
    if column not in df.columns:
        return {"categories": order, "values": [0, 0, 0, 0]}
    counts_raw = df[column].value_counts().to_dict()
    counts = [int(counts_raw.get(level, 0)) for level in order]
    return {"categories": order, "values": counts}


@router.get("/faculty/{faculty_name}/uses-functionality-correlation")
def get_uses_functionality_correlation(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    needed = ["ia_uses", *USES_TASK_COLS]
    df = _filtered_copy(faculty_name, gender, experience, profile, cols=needed)
    if df.empty:
        return []
    missing = [c for c in USES_TASK_COLS if c not in df.columns]
    if missing or "ia_uses" not in df.columns:
        return []

    for col in USES_TASK_COLS:
        df[col] = df[col].map(USES_FREQ_MAP_1TO4)

    means = df.groupby("ia_uses", observed=True)[USES_TASK_COLS].mean(numeric_only=True).rename(columns=USES_NICE_NAMES)
    n_by_group = df.groupby("ia_uses", observed=True).size()
    total_n = float(n_by_group.sum()) or 1.0

    summary = pd.DataFrame(index=means.index)
    summary["usage_label"] = summary.index
    summary["n"] = n_by_group
    summary["pct"] = (n_by_group / total_n) * 100.0
    summary["group_mean"] = means.mean(axis=1)
    summary["group_min"] = means.min(axis=1)
    summary["group_max"] = means.max(axis=1)

    result_df = pd.concat([summary, means], axis=1).reset_index(drop=True)
    result_df = result_df.replace([float("inf"), float("-inf")], None).fillna(0)
    return result_df.to_dict(orient="records")


@router.get("/faculty/{faculty_name}/students-uses-by-proposal")
def students_uses_by_proposal(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    needed = ["ia_proposes_students", *USES_STUDENT_TASK_COLS]
    df = _filtered_copy(faculty_name, gender, experience, profile, cols=needed)
    if df.empty or "ia_proposes_students" not in df.columns:
        return []
    missing = [c for c in USES_STUDENT_TASK_COLS if c not in df.columns]
    if missing:
        return []

    for col in USES_STUDENT_TASK_COLS:
        df[col] = df[col].map(USES_FREQ_MAP_1TO4)

    means = (
        df.groupby("ia_proposes_students", observed=True)[USES_STUDENT_TASK_COLS]
        .mean(numeric_only=True)
        .rename(columns=USES_STUDENT_NICE_NAMES)
    )
    n_by_group = df.groupby("ia_proposes_students", observed=True).size()
    total_n = float(n_by_group.sum()) or 1.0

    summary = pd.DataFrame(index=means.index)
    summary["proposal_label"] = summary.index
    summary["n"] = n_by_group
    summary["pct"] = (n_by_group / total_n) * 100.0
    summary["group_mean"] = means.mean(axis=1)
    summary["group_min"] = means.min(axis=1)
    summary["group_max"] = means.max(axis=1)

    result_df = pd.concat([summary, means], axis=1).reset_index(drop=True)
    result_df = result_df.replace([float("inf"), float("-inf")], None).fillna(0)
    return result_df.to_dict(orient="records")


@router.get("/faculty/{faculty_name}/uses-applications-wordcloud-svg")
def uses_applications_wordcloud_svg(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    svg = _cached_uses_wordcloud_svg(_cache_key(faculty_name, gender, experience, profile))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/uses-applications-distribution-count")
def uses_applications_distribution_count(
        faculty_name: str,
        app_label: str = Query(..., description="Short label (Text/Media/Planning/...)"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)
    if df.empty:
        return {"label": app_label, "levels": ["Never", "Sometimes", "Often", "Very often"], "counts": {}, "total": 0}

    reverse_map = {v: k for k, v in USES_NAME_MAP.items()}
    col = reverse_map.get(app_label)
    if not col:
        raise HTTPException(status_code=400, detail=f"Unknown app_label '{app_label}'")
    if col not in df.columns:
        return {"label": app_label, "levels": ["Never", "Sometimes", "Often", "Very often"], "counts": {}, "total": 0}

    levels = ["Never", "Sometimes", "Often", "Very often"]
    raw = df[col].value_counts().to_dict()
    counts = {lvl: int(raw.get(lvl, 0)) for lvl in levels}
    total = int(sum(counts.values()))
    return {"label": app_label, "levels": levels, "counts": counts, "total": total}


# -----------------------------
# Students adequacy + docchange
# -----------------------------

@router.get("/faculty/{faculty_name}/students-uses-adequacy-distribution")
def students_uses_adequacy_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    col = "ia_uses_adequacy_student"
    if col not in df.columns or df.empty:
        return {"categories": [], "values": [], "total": 0}

    order = ["Unsure", "No misuse", "Appropriate use", "Occasional misuse", "Frequent misuse"]
    vc = df[col].value_counts(dropna=False).to_dict()
    counts = [int(vc.get(label, 0)) for label in order]
    return {"categories": order, "values": counts, "total": int(sum(counts))}


@router.get("/faculty/{faculty_name}/students-docchange-by-adequacy")
def students_docchange_by_adequacy(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    if df.empty or "ia_uses_adequacy_student" not in df.columns:
        return {"adequacy_bins": [], "series": [], "totals_by_bin": []}

    if "ia_uses_docchange_student_list" in df.columns:
        choices_series = df["ia_uses_docchange_student_list"]
    else:
        raw = df["ia_uses_docchange_student"] if "ia_uses_docchange_student" in df.columns else pd.Series(
            [pd.NA] * len(df))

        def _split(x):
            if pd.isna(x):
                return []
            return [p.strip() for p in str(x).split(";") if p.strip()]

        choices_series = raw.apply(_split)

    x = df.copy()
    x["choices"] = choices_series
    x = x[x["ia_uses_adequacy_student"].notna()]
    x = x[x["choices"].apply(lambda xs: bool(xs))]

    if x.empty:
        return {"adequacy_bins": [], "series": [], "totals_by_bin": []}

    adequacy_order = ["Unsure", "No misuse", "Appropriate use", "Occasional misuse", "Frequent misuse"]
    counts_by_choice: Dict[str, Counter] = defaultdict(Counter)

    for _, row in x.iterrows():
        bin_label = str(row["ia_uses_adequacy_student"])
        for choice in row["choices"]:
            counts_by_choice[str(choice)][bin_label] += 1

    present_bins = []
    for b in adequacy_order:
        if sum(c[b] for c in counts_by_choice.values()) > 0:
            present_bins.append(b)

    if not present_bins:
        return {"adequacy_bins": [], "series": [], "totals_by_bin": []}

    docchange_order = [
        "Adapted assessments",
        "Added AI as support",
        "Ethics training",
        "Set course rules",
        "Explicit AI ban",
        "No, considering changes",
        "No changes",
        "Other",
    ]
    used_series = [s for s in docchange_order if any(counts_by_choice[s][b] > 0 for b in present_bins)]

    totals_by_bin = [sum(counts_by_choice[s][b] for s in used_series) for b in present_bins]
    series_out = [{"name": s, "values": [int(counts_by_choice[s][b]) for b in present_bins]} for s in used_series]

    return {"adequacy_bins": present_bins, "series": series_out, "totals_by_bin": totals_by_bin}


# =============================================================================
# Tools wordcloud
# =============================================================================

@router.get("/faculty/{faculty_name}/tools-wordcloud-svg")
def tools_wordcloud_svg(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    svg = _cached_tools_wordcloud_svg(_cache_key(faculty_name, gender, experience, profile))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/tools-wordcount")
def tools_wordcount(
        faculty_name: str,
        tool: str = Query(..., description="Canonical tool label as rendered in the wordcloud"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)
    freq_df = count_tools(df, source_col="ia_uses_tools", unique_per_respondent=True)
    total = int(freq_df["count"].sum()) if not freq_df.empty else 0

    if freq_df.empty:
        return {"tool": tool, "count": 0, "total": 0, "share": 0.0}

    row = freq_df[freq_df["tool"] == tool]
    if row.empty:
        return {"tool": tool, "count": 0, "total": total, "share": 0.0}

    count = int(row["count"].iloc[0])
    share = float(row["share"].iloc[0])
    return {"tool": tool, "count": count, "total": total, "share": share}


# =============================================================================
# Perceptions
# =============================================================================

@router.get("/faculty/{faculty_name}/perceptions-priorities")
def perceptions_priorities(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)
    if "ia_perceptions_doc_priority_list" not in df.columns or df.empty:
        return JSONResponse({"axis": [], "counts": [], "total": 0, "long_map": {}}, status_code=200)

    series = (
        df["ia_perceptions_doc_priority_list"]
        .dropna()
        .explode()
        .value_counts()
        .reindex(PERCEP_PRIORITIES_ORDER, fill_value=0)
    )

    axis = series.index.tolist()
    counts = [int(v) for v in series.values.tolist()]
    total = int(series.sum())

    return {"axis": axis, "counts": counts, "total": total, "long_map": percep_priorities_long_en}


@router.get("/faculty/{faculty_name}/perceptions-students-uses-distribution")
def perceptions_students_uses_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    cats_short = [per_students_use_axis_short_en[c] for c in per_students_use_cols]
    cats_long_map = {per_students_use_axis_short_en[c]: per_students_use_axis_long_en[c] for c in per_students_use_cols}

    series = []
    totals_by_cat = []
    for col in per_students_use_cols:
        col_vals = df[col].dropna() if col in df.columns else pd.Series(dtype=str)
        totals_by_cat.append(int(col_vals.shape[0]))

    for level in LEVELS_ORDER:
        row_counts = []
        for col in per_students_use_cols:
            cnt = int((df[col] == level).sum()) if col in df.columns else 0
            row_counts.append(cnt)
        series.append({"name": level, "values": row_counts})

    return {
        "categories": cats_short,
        "levels": LEVELS_ORDER,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": cats_long_map,
    }


@router.get("/faculty/{faculty_name}/perceptions-students-attitudes-distribution")
def perceptions_students_attitudes_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    if df.empty:
        return {"categories": [], "levels": [], "series": [], "totals_by_cat": [], "long_labels": {}}

    levels = AGREE4_ORDER
    categories: List[str] = []
    totals_by_cat: List[int] = []
    counts_per_level: Dict[str, List[int]] = {lvl: [] for lvl in levels}

    for col in per_students_attitudes_cols:
        short = per_students_attitudes_short_en.get(col, col)
        categories.append(short)

        if col not in df.columns:
            totals_by_cat.append(0)
            for lvl in levels:
                counts_per_level[lvl].append(0)
            continue

        s = df[col].dropna().astype(str)
        total = 0
        for lvl in levels:
            c = int((s == lvl).sum())
            counts_per_level[lvl].append(c)
            total += c
        totals_by_cat.append(total)

    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in levels]
    long_map = {per_students_attitudes_short_en[k]: v for k, v in per_students_attitudes_long_en.items() if
                k in per_students_attitudes_short_en}

    return {"categories": categories, "levels": levels, "series": series, "totals_by_cat": totals_by_cat,
            "long_labels": long_map}


@router.get("/faculty/{faculty_name}/perceptions-tasks-support-distribution")
def perceptions_tasks_support_distribution(
        faculty_name: str,
        domain: str = Query("teaching", pattern="^(teaching|research)$"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    col = "per_ia_tasks_doc" if domain == "teaching" else "per_ia_tasks_rec"
    if col not in df.columns:
        return {"categories": [], "values": [], "domain": domain, "total": 0}

    vc = df[col].value_counts(dropna=True).to_dict()
    categories, values = [], []
    total = 0
    for lab in AGREE4_ORDER:
        v = int(vc.get(lab, 0))
        categories.append(lab)
        values.append(v)
        total += v

    return {"categories": categories, "values": values,
            "domain": "Teaching tasks" if domain == "teaching" else "Research tasks", "total": total}


@router.get("/faculty/{faculty_name}/perceptions-prof-attitude")
def perceptions_prof_attitude(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    col = "PER_IA_POSICPROF_PROH_EV_SUP_INT"
    if col not in df.columns:
        return {"axis": [], "counts": [], "total": 0, "long_map": {}}

    vc = df[col].value_counts(dropna=True).to_dict()
    counts = [int(vc.get(lbl, 0)) for lbl in PROF_ATT_ORDER]
    total = int(sum(counts))

    long_map = {k: PER_PROF_ATT_LONG_EN.get(k, k) for k in PROF_ATT_ORDER}
    return {"axis": PROF_ATT_ORDER, "counts": counts, "total": total, "long_map": long_map}


@router.get("/faculty/{faculty_name}/perceptions-opportunities-risks-distribution")
def perceptions_opportunities_risks_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    cols_present = [c for c in PER_OPORISCUNI_COLS if c in df.columns]
    if not cols_present:
        return {"categories": [], "levels": AGREEMENT4_LEVELS, "series": [], "totals_by_cat": [], "long_labels": {}}

    categories_short = [PER_OPORISCUNI_AXIS_SHORT_EN.get(c, c) for c in cols_present]
    long_map = {PER_OPORISCUNI_AXIS_SHORT_EN.get(c, c): PER_OPORISCUNI_AXIS_LONG_EN.get(c, c) for c in cols_present}

    counts_per_level: Dict[str, List[int]] = {lvl: [] for lvl in AGREEMENT4_LEVELS}
    totals_by_cat: List[int] = []

    for c in cols_present:
        vc = df[c].value_counts(dropna=True).to_dict()
        total_c = sum(int(vc.get(lvl, 0)) for lvl in AGREEMENT4_LEVELS)
        totals_by_cat.append(int(total_c))
        for lvl in AGREEMENT4_LEVELS:
            counts_per_level[lvl].append(int(vc.get(lvl, 0)))

    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in AGREEMENT4_LEVELS]
    return {"categories": categories_short, "levels": AGREEMENT4_LEVELS, "series": series,
            "totals_by_cat": totals_by_cat, "long_labels": long_map}


# =============================================================================
# Training
# =============================================================================

@router.get("/faculty/{faculty_name}/training-received-spider")
def training_received_spider(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    counts_map: Dict[str, int] = {k: 0 for k in TRAINING_RECEIVED_AXIS}
    if "training_received_list" not in df.columns or df.empty:
        return {"axis": TRAINING_RECEIVED_AXIS, "counts": [0] * len(TRAINING_RECEIVED_AXIS), "total": int(df.shape[0]),
                "long_map": training_received_long_en}

    for lst in df["training_received_list"]:
        if isinstance(lst, list):
            for item in lst:
                if item in counts_map:
                    counts_map[item] += 1

    counts = [int(counts_map[k]) for k in TRAINING_RECEIVED_AXIS]
    return {"axis": TRAINING_RECEIVED_AXIS, "counts": counts, "total": int(df.shape[0]),
            "long_map": training_received_long_en}


def compute_training_interest_distribution(
        faculty_name: str,
        gender: Optional[str] = None,
        experience: Optional[str] = None,
        profile: Optional[str] = None,
) -> Dict[str, Any]:
    df = _filtered_view(faculty_name, gender, experience, profile)
    col = "FOR_IA_INTERES"
    if col not in df.columns:
        return {"categories": [], "values": [], "total": 0}

    s = pd.to_numeric(df[col], errors="coerce").dropna().astype("Int64")
    labels = s.map(TRAINING_INTEREST_MAP).dropna()

    counts = labels.value_counts().reindex(TRAINING_INTEREST_ORDER, fill_value=0)
    total = int(counts.sum())
    return {"categories": counts.index.tolist(), "values": counts.values.tolist(), "total": total}


@router.get("/faculty/{faculty}/training-interest-distribution")
def training_interest_distribution(
        faculty: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    return compute_training_interest_distribution(faculty_name=faculty, gender=gender, experience=experience,
                                                  profile=profile)


@router.get("/faculty/{faculty_name}/training-needs-distribution")
def training_needs_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    cols_present = [c for c in TRAINING_NEEDS_COLS if c in df.columns]
    if not cols_present or df.empty:
        return {"categories": [], "levels": AGREEMENT4_LEVELS, "series": [], "totals_by_cat": [], "long_labels": {}}

    cats_short = [TRAINING_NEEDS_AXIS_SHORT_EN.get(c, c) for c in cols_present]
    long_map = {TRAINING_NEEDS_AXIS_SHORT_EN.get(c, c): TRAINING_NEEDS_AXIS_LONG_EN.get(c, c) for c in cols_present}

    counts_per_level: Dict[str, List[int]] = {lvl: [] for lvl in AGREEMENT4_LEVELS}
    totals_by_cat: List[int] = []

    for c in cols_present:
        vc = df[c].value_counts(dropna=True).to_dict()
        total_c = sum(int(vc.get(lvl, 0)) for lvl in AGREEMENT4_LEVELS)
        totals_by_cat.append(int(total_c))
        for lvl in AGREEMENT4_LEVELS:
            counts_per_level[lvl].append(int(vc.get(lvl, 0)))

    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in AGREEMENT4_LEVELS]
    return {"categories": cats_short, "levels": AGREEMENT4_LEVELS, "series": series, "totals_by_cat": totals_by_cat,
            "long_labels": long_map}


# =============================================================================
# Open text routes (aggregates + items)
# =============================================================================

@router.get("/open_text/perceptions/opportunities")
def open_text_perceptions_opportunities(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_aggregates("per_ia_oporiscuni_altres", faculty)


@router.get("/open_text/perceptions/positioning")
def open_text_perceptions_positioning(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_aggregates("per_ia_posicprof_perque", faculty)


@router.get("/open_text/training/other_needs")
def open_text_training_other_needs(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_aggregates("for_ia_neceformat_altres", faculty)


@router.get("/open_text/comments")
def open_text_general_comments(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_aggregates("comments", faculty)


@router.get("/open_text/perceptions/opportunities/items")
def open_text_perceptions_opportunities_items(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_items("per_ia_oporiscuni_altres", faculty)


@router.get("/open_text/perceptions/positioning/items")
def open_text_perceptions_positioning_items(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_items("per_ia_posicprof_perque", faculty)


@router.get("/open_text/training/other_needs/items")
def open_text_training_other_needs_items(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_items("for_ia_neceformat_altres", faculty)


@router.get("/open_text/comments/items")
def open_text_general_comments_items(
        faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return _open_text_items("comments", faculty)
