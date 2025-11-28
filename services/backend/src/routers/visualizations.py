from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any, Literal, List
from fastapi.responses import JSONResponse
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np
import math
import pandas as pd
import os
import numpy as np
import logging
from matplotlib import cm, colors
from src.utils.tools_normalizer import count_tools

from src.utils.data_loader import (
    load_surveys_data, load_faculties_data, df_to_json_safe, PERCEP_PRIORITIES_ORDER,
    percep_priorities_long_en,
    per_students_use_cols, per_students_use_level_mapping,
    per_students_use_axis_short_en, per_students_use_axis_long_en,
    per_students_attitudes_cols, per_students_attitudes_short_en, per_students_attitudes_long_en,
    per_prof_attitude_long_en,
    PER_OPORISCUNI_COLS, PER_OPORISCUNI_AXIS_SHORT_EN, PER_OPORISCUNI_AXIS_LONG_EN,
    AGREEMENT4_LEVELS,
    TRAINING_RECEIVED_AXIS, training_received_long_en,
    TRAINING_INTEREST_MAP, TRAINING_INTEREST_ORDER,
    TRAINING_NEEDS_COLS, TRAINING_NEEDS_AXIS_SHORT_EN, TRAINING_NEEDS_AXIS_LONG_EN,
)
from src.utils.open_text_agent import load_open_text_analysis

PER_PROF_ATT_LONG_EN = per_prof_attitude_long_en

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api", tags=["Visualizations"])

# Load once at startup
faculties_df = load_faculties_data()
surveys_df = load_surveys_data()

SCORE_COLS = ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
LEVELS_ORDER = [
    "Not at all",
    "A little",
    "Quite a bit",
    "A lot",
    "Don't know",
]

LEVEL_ORDER = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]
# Stable order for radar
PROF_ATT_ORDER = ["Prohibit", "Avoid", "Overcome", "Integrate"]


def safe_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except Exception:
        return None


def mean_ignore_none(values):
    vals = [v for v in values if isinstance(v, (int, float))]
    if not vals:
        return None
    return sum(vals) / len(vals)


# Cache in-memory on startup (or load lazily if you prefer)
SURVEYS_DF: pd.DataFrame = load_surveys_data()
try:
    FACULTIES_DF: pd.DataFrame = load_faculties_data()
except Exception:
    FACULTIES_DF = pd.DataFrame(columns=["faculty_name"])

OPEN_TEXT_ANALYSIS = load_open_text_analysis()

# --- Helpers --------------------------------------------------------------

GENDER_ORDER = ["Female", "Male", "Non-binary", "No answer"]
PROFILE_ORDER = ["Senior Lecturer", "Associate", "PreDoc", "PostDoc", "Collab", "Lecturer", "Professor"]
EXPERIENCE_ORDER = ["Less than 5", "Between 5 and 10", "Between 11 and 20", "More than 20"]
MODE_ORDER = ["In-person", "Online", "Hybrid", "In-person+Online", "In-person+Hybrid", "All modes"]


def _counts_for_column(df: pd.DataFrame, col: str, order: List[str] | None = None) -> Dict[str, Any]:
    if col not in df.columns:
        return {"categories": [], "counts": []}
    vc = (
        df[col]
        .dropna()
        .astype(str)
        .value_counts()
        .to_dict()
    )
    if order:
        cats = [c for c in order if vc.get(c, 0) > 0]
        cnts = [vc[c] for c in cats]
    else:
        # natural order by count desc
        items = sorted(vc.items(), key=lambda x: (-x[1], x[0]))
        cats = [k for k, _ in items]
        cnts = [v for _, v in items]
    return {"categories": cats, "counts": cnts}


def _age_counts(df: pd.DataFrame) -> Dict[str, Any]:
    if "age" not in df.columns:
        return {"categories": [], "counts": []}

    # Coerce age to numeric (handles strings like "34")
    ages = pd.to_numeric(df["age"], errors="coerce")

    # Robust bins with no duplicate edges
    bins = [-np.inf, 20, 30, 40, 50, 60, 70, np.inf]
    labels = ["<20", "20s", "30s", "40s", "50s", "60s", "70+"]

    cut = pd.cut(
        ages,
        bins=bins,
        labels=labels,
        right=False,  # 20 goes into [20,30) -> "20s"
        include_lowest=True,
        duplicates="drop",  # belt-and-suspenders, avoids the crash
    )

    vc = cut.value_counts().to_dict()

    # Only show the requested buckets on the X-axis
    wanted = ["20s", "30s", "40s", "50s", "60s", "70+"]
    cats = [lbl for lbl in wanted if vc.get(lbl, 0) > 0]
    cnts = [int(vc.get(lbl, 0)) for lbl in cats]

    return {"categories": cats, "counts": cnts}


def _df_by_faculty(df: pd.DataFrame, faculty: Optional[str]) -> pd.DataFrame:
    if not faculty:
        return df
    fac_key = str(faculty).strip().lower()
    return df[df["faculty_name"].astype(str).str.strip().str.lower() == fac_key]

def _open_text_aggregates(question_id: str, faculty: Optional[str]) -> Dict[str, Any]:
    if question_id not in OPEN_TEXT_ANALYSIS:
        return {
            "sentiment": {"labels": [], "counts": []},
            "topics": {"labels": [], "counts": []},
        }

    df_anal = OPEN_TEXT_ANALYSIS[question_id]
    if df_anal.empty:
        return {
            "sentiment": {"labels": [], "counts": []},
            "topics": {"labels": [], "counts": []},
        }

    df_surv = SURVEYS_DF[["row_id", "faculty_name"]].copy()
    df = df_anal.merge(df_surv, on="row_id", how="left")

    if faculty:
        fac_key = str(faculty).strip().lower()
        df = df[df["faculty_name"].astype(str).str.strip().str.lower() == fac_key]

    if df.empty:
        return {
            "sentiment": {"labels": [], "counts": []},
            "topics": {"labels": [], "counts": []},
        }

    # sentiment
    sent_vc = df["sentiment"].value_counts().to_dict()
    sent_order = ["negative", "neutral", "positive"]
    sent_labels = [s for s in sent_order if s in sent_vc]
    sent_counts = [int(sent_vc[s]) for s in sent_labels]

    # topics (cluster_label)
    topic_vc = df.groupby("cluster_label")["row_id"].count().sort_values(ascending=False)
    topic_labels = list(topic_vc.index)
    topic_counts = [int(v) for v in topic_vc.values]

    return {
        "sentiment": {"labels": sent_labels, "counts": sent_counts},
        "topics": {"labels": topic_labels, "counts": topic_counts},
    }



# --- Routes ---------------------------------------------------------------

@router.get("/survey/summary")
def survey_summary(
    faculty: Optional[str] = Query(None, description="Optional faculty name (short EN) to filter responses")
) -> Dict[str, Any]:
    df = _df_by_faculty(SURVEYS_DF, faculty)
    total_responses = int(len(df))
    # keep total faculties global so the KPI remains comparable
    total_faculties = int(SURVEYS_DF["faculty_name"].nunique())
    return {"total_responses": total_responses, "total_faculties": total_faculties}



@router.get("/survey/distribution")
def survey_distribution(
    category: Literal["age", "gender", "profile", "experience", "mode"] = Query(..., description="Which dimension"),
    faculty: Optional[str] = Query(None, description="Optional faculty filter")
) -> Dict[str, Any]:
    base = _df_by_faculty(SURVEYS_DF, faculty)
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
    if SURVEYS_DF.empty or "faculty_name" not in SURVEYS_DF.columns:
        return {"faculties": [], "total": 0}

    vc = (
        SURVEYS_DF["faculty_name"]
        .dropna()
        .astype(str)
        .value_counts()
        .sort_index()
    )
    rows = [
        {"faculty_name": name, "responses": int(count)}
        for name, count in vc.items()
        if int(count) >= int(min_count)
    ]
    return {"faculties": rows, "total": int(sum(r["responses"] for r in rows))}


@router.get("/faculty/{faculty_name}/scores")
def faculty_scores(
        faculty_name: str,
        gender: str | None = None,
        teaching_experience: str | None = None,
        ub_profile: str | None = None,
) -> Dict[str, Any]:
    df = surveys_df.copy()

    # Apply the same optional filters used by /spike-map
    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # Case/space-insensitive faculty match over ALL rows for that faculty
    fac_key = (faculty_name or "").strip().lower()
    mask = df["faculty_name"].astype(str).str.strip().str.lower() == fac_key
    if not mask.any():
        raise HTTPException(status_code=404, detail=f"Faculty '{faculty_name}' not found")

    fdf = df.loc[mask].copy()

    # Match /spike-map math for "All":
    # 1) per-row mean across the 4 columns
    fdf["row_mean"] = fdf[SCORE_COLS].mean(axis=1, skipna=True)
    # 2) overall faculty score = mean of those per-row means
    total_score = float(fdf["row_mean"].mean(skipna=True))

    # Per-metric means across all rows for this faculty
    metric_means = fdf[SCORE_COLS].mean(numeric_only=True, skipna=True).to_dict()
    metric_means = {k: (float(v) if v is not None else None) for k, v in metric_means.items()}

    # Color: prefer faculties_df if present; otherwise take first non-null in fdf
    color = None
    if "faculties_df" in globals():
        meta = faculties_df[
            faculties_df["faculty_name"].astype(str).str.strip().str.lower() == fac_key
            ]
        if not meta.empty and "color" in meta.columns:
            color = meta["color"].dropna().iloc[0] if not meta["color"].dropna().empty else None

    if color is None and "color" in fdf.columns and not fdf["color"].dropna().empty:
        color = fdf["color"].dropna().iloc[0]

    return {
        "faculty_name": fdf["faculty_name"].iloc[0],
        "color": color,
        **metric_means,  # knowledge_score, uses_score, perceptions_score, training_needs_score
        "total_score": total_score,  # mean(row_means) — matches /spike-map when category=All
    }


@router.get("/treemap-data")
def get_treemap_data(
        gender: str | None = None,
        teaching_experience: str | None = None,
        ub_profile: str | None = None,
):
    """
    Clean aggregated dataset for the treemap / bubble chart.

    We return one row per faculty x dimension ("Knowledge", "Uses", "Perceptions", "Training"),
    with:
      - value: that faculty's mean score for that dimension
      - overall_faculty_score: mean of all 4 dims for that faculty (for coloring, etc.)

    IMPORTANT:
    We DROP faculties where all four dim scores are 0.0.
    That prevents Plotly treemap from crashing when it tries to
    compute weighted averages with zero total weight.
    """
    df = surveys_df.copy()

    # ----- apply optional demographic filters -----
    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # if after filters no rows, just return empty list
    if df.empty:
        return []

    # ----- compute mean scores per faculty -----
    score_cols = [
        "knowledge_score",
        "uses_score",
        "perceptions_score",
        "training_needs_score",
    ]

    fac_means = (
        df.groupby("faculty_name")[score_cols]
        .mean(numeric_only=True)
        .reset_index()
    )

    # replace NaN/inf with 0.0 so we can reason about "has data vs no data"
    fac_means = fac_means.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # compute per-faculty overall avg (across the 4 dims)
    fac_means["overall_faculty_score"] = fac_means[
        ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
    ].mean(axis=1)

    # bring metadata (color, etc.) from faculties_df
    fac_means = fac_means.merge(
        faculties_df[["faculty_name", "color", "color_rgb", "short_name"]],
        on="faculty_name",
        how="left",
    )

    rows = []

    for _, row in fac_means.iterrows():
        faculty = row["faculty_name"]

        k = float(row["knowledge_score"])
        u = float(row["uses_score"])
        p = float(row["perceptions_score"])
        t = float(row["training_needs_score"])

        # detect "no data at all for this faculty after filters"
        # note: true scores should NEVER be literally 0
        # (your scoring is on a positive scale),
        # so 0 basically means "missing → filled with 0"
        if (k == 0.0) and (u == 0.0) and (p == 0.0) and (t == 0.0):
            # skip this faculty entirely so Plotly doesn't freak out
            continue

        overall_val = float(row["overall_faculty_score"])
        if not np.isfinite(overall_val):
            overall_val = 0.0

        dim_map = [
            ("Knowledge", k),
            ("Uses", u),
            ("Perceptions", p),
            ("Training", t),
        ]

        for dim_label, dim_val in dim_map:
            # if for some reason this specific dim is still weird, coerce
            if (not np.isfinite(dim_val)) or pd.isna(dim_val):
                dim_val = 0.0

            rows.append({
                # hierarchy info for the treemap
                "faculty_name": faculty,  # parent node in px.treemap path[0]
                "label": dim_label,  # child node name (path[1])
                "value": float(dim_val),  # size of the child block

                # extra stuff frontend can use for color / hover
                "overall_faculty_score": overall_val,
                "short_name": row.get("short_name", faculty),
                "color": row.get("color", None),
                "color_rgb": row.get("color_rgb", None),
            })

    # if all faculties got skipped, return empty clean array
    if not rows:
        return []

    out_df = pd.DataFrame(rows)

    # sanitize: ensure no NaN/inf in final JSON
    out_df = out_df.replace([np.inf, -np.inf], np.nan)
    out_df = out_df.fillna(0.0)

    return df_to_json_safe(out_df)


@router.get("/spike-map")
def get_spike_map_data(
        category: str = "All",
        gender: str | None = None,
        teaching_experience: str | None = None,
        ub_profile: str | None = None,
):
    df = surveys_df.copy()

    # ----- filters -----
    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # ----- pick/compute category_score for each row -----
    if category == "All":
        df["category_score"] = df[
            ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
        ].mean(axis=1)
    else:
        category_column = {
            "knowledge": "knowledge_score",
            "uses": "uses_score",
            "perceptions": "perceptions_score",
            "training": "training_needs_score",
        }.get(category, "knowledge_score")
        df["category_score"] = df[category_column]

    # ----- attach faculty metadata (lat/lon/color/etc) -----
    faculties_df["color_rgb_tuple"] = faculties_df["color_rgb"].apply(tuple)
    df = df.merge(faculties_df, on="faculty_name", how="left")

    # ----- aggregate by faculty -----
    agg = df.groupby(
        ["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb_tuple"],
        dropna=False,
    ).agg(
        {
            "category_score": "mean",
            "knowledge_score": "mean",
            "uses_score": "mean",
            "perceptions_score": "mean",
            "training_needs_score": "mean",
            "faculty_name": "count",
        }
    )

    agg = agg.rename(columns={"faculty_name": "n_responses"}).reset_index()

    # ----- convert rgb tuple back to list for JSON -----
    agg["color_rgb"] = agg["color_rgb_tuple"].apply(list)
    agg.drop(columns=["color_rgb_tuple"], inplace=True)

    return df_to_json_safe(agg)


@router.get("/faculty/{faculty_name}/knowledge-distribution")
def knowledge_distribution(
        faculty_name: str,
        demographic1: str = "gender",
        demographic2: str | None = None,
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Map textual knowledge → numeric 1–4
    knowledge_map = {
        "No knowledge": 1,
        "Little knowledge": 2,
        "Good knowledge": 3,
        "Expert knowledge": 4,
    }
    df["knowledge_num"] = df["ia_knowledge"].map(knowledge_map)

    col_map = {
        "gender": "gender",
        "experience": "teaching_experience",
        "profile": "ub_profile",
    }
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    # Single demographic → mean per category (normalized)
    if not col2:
        grouped = (
            df.groupby(col1)["knowledge_num"]
            .mean()
            .reset_index()
            .rename(columns={col1: "category", "knowledge_num": "average_score"})
        )
        grouped["average_score"] = grouped["average_score"].astype(float).round(3)
        return {
            "mode": "single",
            "demographics": [demographic1],
            "categories": grouped["category"].tolist(),
            "values": grouped["average_score"].tolist(),
        }

    # Dual demographic:
    g = (
        df.groupby([col1, col2])["knowledge_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    # total respondents per main group
    g["n_main"] = g.groupby("main")["n_sub"].transform("sum")

    # main-group average
    main_avg_map = df.groupby(col1)["knowledge_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # weighted contribution so sum_sub(contrib)==main_avg
    g["contribution"] = (g["mean_sub"] * g["n_sub"]) / g["n_main"]
    g = g.fillna(0.0)

    for c in ["mean_sub", "main_avg", "contribution"]:
        g[c] = g[c].astype(float)

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]]
        .to_dict(orient="records"),
    }


def get_sankey_chart_data():
    df = surveys_df.copy()

    # ---- sanitize NA in categoricals for the Sankey ----
    # (You already fill gender in the loader; this is extra safety at runtime.)
    for col, filler in [("gender", "No answer"),
                        ("teaching_experience", None),
                        ("ub_profile", None)]:
        if col in df.columns:
            if filler is None:
                df[col] = df[col].dropna()
            else:
                df[col] = df[col].fillna(filler)

    # Build third-layer vocabularies WITHOUT NA
    genders = [v for v in df["gender"].unique() if pd.notna(v)]
    exps = [v for v in df["teaching_experience"].unique() if pd.notna(v)]
    profiles = [v for v in df["ub_profile"].unique() if pd.notna(v)]

    # All node labels (layers of the Sankey)
    labels = (
            ["Knowledge", "Uses", "Perceptions", "Training Needs"]  # 0..3
            + ["Gender", "Teaching Experience", "UB Profile"]  # 4..6
            + list(map(str, genders))
            + list(map(str, exps))
            + list(map(str, profiles))
            + faculties_df["faculty_name"].astype(str).tolist()
    )

    # Fast lookup (avoid list.index() on sequences containing pd.NA)
    label_to_idx = {str(lbl): i for i, lbl in enumerate(labels)}

    # First layer indices (scores)
    first_layer_indices = {
        "knowledge_score": 0,
        "uses_score": 1,
        "perceptions_score": 2,
        "training_needs_score": 3,
    }

    # Second layer indices (category blocks)
    # positions 4,5,6 correspond to the 3 blocks added above
    second_layer_indices = {
        "gender": 4,
        "teaching_experience": 5,
        "ub_profile": 6,
    }

    # Third layer indices (subgroups)
    third_layer_indices = {
        **{str(g): label_to_idx[str(g)] for g in genders},
        **{str(e): label_to_idx[str(e)] for e in exps},
        **{str(p): label_to_idx[str(p)] for p in profiles},
    }

    # Faculty indices
    faculty_indices = {
        str(f): label_to_idx[str(f)]
        for f in faculties_df["faculty_name"].astype(str).tolist()
    }

    sources, targets, values = [], [], []

    # (1) score dimension -> demographic category block
    for score in ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]:
        for category, cat_idx in second_layer_indices.items():
            # groupby automatically ignores NaNs in keys
            category_score = df.groupby(category)[score].sum(numeric_only=True).sum()
            sources.append(first_layer_indices[score])
            targets.append(cat_idx)
            values.append(float(category_score) if pd.notna(category_score) else 0.0)

    # (2) demographic category block -> specific subgroup
    for category, cat_idx in second_layer_indices.items():
        grouped_scores = (
            df.groupby(category)[["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]]
            .sum(numeric_only=True)
        )
        for subgroup_value, scores in grouped_scores.iterrows():
            if pd.isna(subgroup_value):
                continue
            sv = str(subgroup_value)
            if sv not in third_layer_indices:
                continue
            sources.append(cat_idx)
            targets.append(third_layer_indices[sv])
            values.append(float(scores.sum()) if pd.notna(scores.sum()) else 0.0)

    # (3) subgroup -> faculty
    for _, row in df.iterrows():
        faculty = row.get("faculty_name")
        if pd.isna(faculty):
            continue
        fac_key = str(faculty)
        if fac_key not in faculty_indices:
            continue

        faculty_score = sum(
            float(row.get(col, 0.0)) if pd.notna(row.get(col)) else 0.0
            for col in ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
        )

        for category in ["gender", "teaching_experience", "ub_profile"]:
            subgroup_value = row.get(category)
            if pd.isna(subgroup_value):
                continue
            sv = str(subgroup_value)
            if sv not in third_layer_indices:
                continue
            sources.append(third_layer_indices[sv])
            targets.append(faculty_indices[fac_key])
            values.append(faculty_score)

    # Faculty colors (guard against missing)
    faculty_colors = {}
    for faculty in faculties_df["faculty_name"].astype(str):
        row = faculties_df.loc[faculties_df["faculty_name"].astype(str) == faculty]
        color = None
        if not row.empty and "color" in row.columns:
            _ser = row["color"].dropna()
            color = _ser.iloc[0] if not _ser.empty else None
        faculty_colors[str(faculty)] = str(color) if color is not None else "#999999"

    # Sanitize numeric lists
    def _sanitize_num_list(seq):
        out = []
        for x in seq:
            if isinstance(x, (np.integer,)):
                x = int(x)
            elif isinstance(x, (np.floating,)):
                x = float(x)
            if isinstance(x, float) and not math.isfinite(x):
                x = 0.0
            out.append(x)
        return out

    return {
        "sources": _sanitize_num_list(sources),
        "targets": _sanitize_num_list(targets),
        "values": _sanitize_num_list(values),
        "labels": [str(x) for x in labels],
        "faculty_colors": {str(k): str(v) for k, v in faculty_colors.items()},
    }


@router.get("/sankey-data")
def sankey_data():
    """
    Return data for Sankey chart (faculty, gender, experience, etc.),
    with NaN/Inf already cleaned.
    """
    data = get_sankey_chart_data()
    # Nothing fancy here because we already sanitized in get_sankey_chart_data()
    return data


@router.get("/faculty/{faculty_name}/normative-distribution")
def get_normative_distribution(faculty_name: str):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name]

    column = "ia_normative_ub"
    distribution = df[column].value_counts().to_dict()

    return {
        "categories": list(distribution.keys()),
        "values": list(distribution.values())
    }


@router.get("/faculty/{faculty_name}/knowledge-functionality-correlation")
def get_knowledge_functionality_correlation(
    faculty_name: str,
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Apply demographic filters
    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # If no data after filters: return empty list, frontend already handles this
    if df.empty:
        return []

    # 13 application columns (knowledge familiarity)
    app_cols = [
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

    # Map likert → numeric 1–4
    app_map = {
        "I don't know any": 1,
        "I know a few": 2,
        "I know several": 3,
        "I know many": 4,
    }

    for col in app_cols:
        df[col] = df[col].map(app_map)

    # Drop rows with missing global knowledge label
    df = df.dropna(subset=["ia_knowledge"])
    if df.empty:
        return []

    total_n = len(df)

    # Mean familiarity for each application within each global knowledge level
    grouped_means = df.groupby("ia_knowledge")[app_cols].mean()

    # Count respondents per global knowledge level
    group_counts = df.groupby("ia_knowledge").size()

    # Compute overall stats across the 13 applications per group
    group_mean = grouped_means.mean(axis=1)
    group_min = grouped_means.min(axis=1)
    group_max = grouped_means.max(axis=1)
    group_pct = (group_counts / float(total_n)) * 100.0 if total_n > 0 else 0.0

    # Build result DataFrame
    result_df = grouped_means.copy()
    result_df["n"] = group_counts.astype(int)
    result_df["pct"] = group_pct
    result_df["group_mean"] = group_mean
    result_df["group_min"] = group_min
    result_df["group_max"] = group_max

    # Move ia_knowledge to a proper column and rename to knowledge_label
    result_df = result_df.reset_index().rename(columns={"ia_knowledge": "knowledge_label"})

    # Ensure column order: label + 13 apps (for your frontend matrix) + stats
    result_df = result_df[
        ["knowledge_label"]
        + app_cols
        + ["n", "pct", "group_mean", "group_min", "group_max"]
    ]

    # Clean weird numeric values (NaN, inf) → 0
    numeric_cols = app_cols + ["n", "pct", "group_mean", "group_min", "group_max"]
    result_df[numeric_cols] = result_df[numeric_cols].replace([math.inf, -math.inf], 0).fillna(0)

    return result_df.to_dict(orient="records")

def truncate_colormap(cmap_name: str, minval=0.4, maxval=1.0, n=256):
    """
    Take an existing matplotlib colormap (e.g. "Purples") and
    return a new one that only spans [minval, maxval] of it.
    minval closer to 0 = include more of the light pastels
    minval closer to 1 = only deep, dark end.
    """
    base = cm.get_cmap(cmap_name)
    new_colors = base(np.linspace(minval, maxval, n))
    return colors.LinearSegmentedColormap.from_list(
        f"{cmap_name}_trunc_{minval}_{maxval}",
        new_colors
    )


purples_trunc = truncate_colormap("Purples", minval=0.4, maxval=1.0)
reds_trunc = truncate_colormap("Reds", minval=0.4, maxval=1.0)


@router.get("/faculty/{faculty_name}/knowledge-applications-wordcloud-svg")
def knowledge_concept_cloud_image(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    app_map = {
        "I don't know any": 1,
        "I know a few": 2,
        "I know several": 3,
        "I know many": 4,
    }

    app_columns = [
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

    name_map = {
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

    for col in app_columns:
        df[col] = df[col].map(app_map).fillna(0)

    total_scores = df[app_columns].sum().to_dict()

    # Visual boost
    gamma = 1.25
    freqs = {name_map[c]: float(v) ** gamma for c, v in total_scores.items()}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "..", "img")
    os.makedirs(img_dir, exist_ok=True)
    output_path = os.path.join(img_dir, f"{faculty_name}_wordcloud.png")

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

    svg = wc.to_svg(embed_font=True)
    svg = svg.replace(
        "<svg ",
        "<svg style='max-width:100%;height:auto' "
    )
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s} text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}</style></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/knowledge-applications-distribution-count")
def knowledge_app_distribution(
        faculty_name: str,
        app_label: str = Query(..., description="Label from name_map, e.g. 'Text', 'Media', ..."),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    name_map = {
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
    reverse_name_map = {v: k for k, v in name_map.items()}
    col = reverse_name_map.get(app_label)
    if not col:
        raise HTTPException(status_code=400, detail=f"Unknown app_label '{app_label}'")

    levels = ["I don't know any", "I know a few", "I know several", "I know many"]

    counts = {lvl: int((df[col] == lvl).sum()) for lvl in levels}
    total = int(sum(counts.values()))

    return {"label": app_label, "levels": levels, "counts": counts, "total": total}


# ---------------------------------------------------------------------------------
# NEW ENDPOINTS FOR THE "USES" SECTION
# ---------------------------------------------------------------------------------

@router.get("/faculty/{faculty_name}/uses-distribution")
def uses_distribution(
        faculty_name: str,
        demographic1: str = "gender",
        demographic2: str | None = None,
):
    """
    Same shape/logic as /knowledge-distribution but for AI usage.
    We treat self-reported global usage level (ia_uses) as 1..4.
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Map textual usage → numeric 1–4
    uses_map = {
        "No use": 1,
        "Low use": 2,
        "Moderate use": 3,
        "Advanced use": 4,
    }
    df["uses_num"] = df["ia_uses"].map(uses_map)

    col_map = {
        "gender": "gender",
        "experience": "teaching_experience",
        "profile": "ub_profile",
    }
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    # Single demographic
    if not col2:
        grouped = (
            df.groupby(col1)["uses_num"]
            .mean()
            .reset_index()
            .rename(columns={col1: "category", "uses_num": "average_score"})
        )
        grouped["average_score"] = grouped["average_score"].astype(float).round(3)
        return {
            "mode": "single",
            "demographics": [demographic1],
            "categories": grouped["category"].tolist(),
            "values": grouped["average_score"].tolist(),
        }

    # Two demographics
    g = (
        df.groupby([col1, col2])["uses_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    g["n_main"] = g.groupby("main")["n_sub"].transform("sum")

    main_avg_map = df.groupby(col1)["uses_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # Weighted contribution so sum_sub(contribution) == main_avg
    g["contribution"] = (g["mean_sub"] * g["n_sub"]) / g["n_main"]
    g = g.fillna(0.0)

    for c in ["mean_sub", "main_avg", "contribution"]:
        g[c] = g[c].astype(float)

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[
            ["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]
        ].to_dict(orient="records"),
    }


@router.get("/faculty/{faculty_name}/proposes-distribution")
def get_proposes_distribution(faculty_name: str):
    """
    Pie chart for: 'Do they propose AI use to students?'
    We look at ia_proposes_students which is already mapped to:
    "Never", "Sometimes", "Often", "Very often".
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    column = "ia_proposes_students"
    order = ["Never", "Sometimes", "Often", "Very often"]

    counts_raw = df[column].value_counts().to_dict()
    counts = [int(counts_raw.get(level, 0)) for level in order]

    return {
        "categories": order,
        "values": counts,
    }


@router.get("/faculty/{faculty_name}/uses-functionality-correlation")
def get_uses_functionality_correlation(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Mirror of /knowledge-functionality-correlation but for usage frequency.

    For each global usage level (ia_uses), compute:
      - mean usage (1..4) for each task
      - n of respondents in that level
      - pct within the faculty
      - group_mean / group_min / group_max across all tasks

    Returns one row per usage level:
      {
        "usage_label": "Low use",
        "n": 12,
        "pct": 30.0,
        "group_mean": 2.10,
        "group_min": 1.00,
        "group_max": 3.40,
        "Text Creation": <float>,
        ...
      }
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Filters
    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # If nothing left, bail early
    if df.empty:
        return []

    # task columns (do NOT include ia_proposes_students here)
    task_cols = [
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

    # map frequency to 1..4 numeric
    task_freq_to_1to4 = {
        "Never": 1.0,
        "Sometimes": 2.0,
        "Often": 3.0,
        "Very often": 4.0,
    }

    for col in task_cols:
        df[col] = df[col].map(task_freq_to_1to4)

    # Means per usage level
    means = df.groupby("ia_uses")[task_cols].mean()

    # Counts per usage level
    n_by_group = df.groupby("ia_uses").size()
    total_n = float(n_by_group.sum()) or 1.0

    # Nice display names
    nice_names = {
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
    means = means.rename(columns=nice_names)

    # Summary stats across tasks for each usage level
    summary = pd.DataFrame(index=means.index)
    summary["usage_label"] = summary.index
    summary["n"] = n_by_group
    summary["pct"] = (n_by_group / total_n * 100.0)
    summary["group_mean"] = means.mean(axis=1)
    summary["group_min"] = means.min(axis=1)
    summary["group_max"] = means.max(axis=1)

    # Combine summary + per-task means
    result_df = pd.concat([summary, means], axis=1).reset_index(drop=True)

    # clean up NaN / inf
    result_df = result_df.replace([float("inf"), float("-inf")], None).fillna(0)

    return result_df.to_dict(orient="records")
@router.get("/faculty/{faculty_name}/students-uses-by-proposal")
def students_uses_by_proposal(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Like /uses-functionality-correlation but:
      - task columns are the *_student ones
      - groups are ia_proposes_students ∈ {"Never","Sometimes","Often","Very often"}

    For each proposal bucket we return:
      {
        "proposal_label": "Never" | "Sometimes" | "Often" | "Very often",
        "n": <int>,                  # respondents in this bucket
        "pct": <float>,              # share in %
        "group_mean": <float>,       # mean across all tasks
        "group_min": <float>,        # min across tasks
        "group_max": <float>,        # max across tasks
        "Text Creation": <float>,    # per-task averages (1..4)
        ...
      }
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Optional demographic filters
    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    if df.empty:
        return []

    if "ia_proposes_students" not in df.columns:
        return []

    # --- students task columns (11) ---
    task_cols = [
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

    # map short display names
    nice_names = {
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

    # frequency → numeric (1..4)
    freq_to_1to4 = {
        "Never": 1.0,
        "Sometimes": 2.0,
        "Often": 3.0,
        "Very often": 4.0,
    }

    # Coerce tasks to numeric 1..4
    for col in task_cols:
        if col in df.columns:
            df[col] = df[col].map(freq_to_1to4)

    # Means per proposal bucket
    means = df.groupby("ia_proposes_students")[task_cols].mean(numeric_only=True)

    # Counts per bucket
    n_by_group = df.groupby("ia_proposes_students").size()
    total_n = float(n_by_group.sum()) or 1.0

    # Summary stats across tasks for each proposal bucket
    summary = pd.DataFrame(index=means.index)
    summary["proposal_label"] = summary.index
    summary["n"] = n_by_group
    summary["pct"] = (n_by_group / total_n) * 100.0
    summary["group_mean"] = means.mean(axis=1)
    summary["group_min"] = means.min(axis=1)
    summary["group_max"] = means.max(axis=1)

    # Rename tasks for frontend
    means = means.rename(columns=nice_names)

    # Combine summary + per-task means
    result_df = pd.concat([summary, means], axis=1).reset_index(drop=True)

    # sanitize numerics
    result_df = result_df.replace([float("inf"), float("-inf")], None).fillna(0)

    # return as list-of-records
    return result_df.to_dict(orient="records")


@router.get("/faculty/{faculty_name}/uses-applications-wordcloud-svg")
def uses_applications_wordcloud_svg(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Wordcloud for "Where is AI actually being used?"
    We look at usage frequency for each task column, map it to 1..4,
    sum across respondents, and feed that to a WordCloud.
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # task columns (usage), excluding proposes-to-students
    app_columns = [
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

    # short display names for each task in the cloud
    name_map = {
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

    freq_map = {
        "Never": 1,
        "Sometimes": 2,
        "Often": 3,
        "Very often": 4,
    }

    for col in app_columns:
        df[col] = df[col].map(freq_map).fillna(0)

    total_scores = df[app_columns].sum().to_dict()

    # amplify a bit so differences pop visually
    gamma = 1.25
    freqs = {name_map[c]: float(v) ** gamma for c, v in total_scores.items()}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "..", "img")
    os.makedirs(img_dir, exist_ok=True)
    output_path = os.path.join(img_dir, f"{faculty_name}_uses_wordcloud.png")

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
        colormap=purples_trunc,  # purple theme for Uses
    ).generate_from_frequencies(freqs)

    svg = wc.to_svg(embed_font=True)
    svg = svg.replace(
        "<svg ",
        "<svg style='max-width:100%;height:auto' "
    )
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s} text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}</style></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/uses-applications-distribution-count")
def uses_applications_distribution_count(
        faculty_name: str,
        app_label: str = Query(..., description="Short label from name_map (e.g. 'Text', 'Media', etc.)"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Tooltip spiderchart for Uses wordcloud.
    Given a task label like 'Text', return how many respondents said
    Never / Sometimes / Often / Very often for that task.
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # same map we used in the wordcloud endpoint above
    name_map = {
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
    reverse_name_map = {v: k for k, v in name_map.items()}
    col = reverse_name_map.get(app_label)
    if not col:
        raise HTTPException(status_code=400, detail=f"Unknown app_label '{app_label}'")

    # fixed order so front-end spider chart can trust it
    levels = ["Never", "Very often", "Sometimes", "Often"]
    # NOTE: our tooltip spider in UsesApplicationsWordCloud
    # plots POLAR_ORDER = ["Never", "Very often", "Sometimes", "Often"]
    # so we match that exact set here. We'll still count using canonical 4 buckets.

    canonical_levels = ["Never", "Sometimes", "Often", "Very often"]
    raw_counts = df[col].value_counts().to_dict()

    # Build counts dict covering all 4 canonical levels
    counts_dict = {lvl: int(raw_counts.get(lvl, 0)) for lvl in canonical_levels}
    total = int(sum(counts_dict.values()))

    return {
        "label": app_label,
        "levels": canonical_levels,
        "counts": counts_dict,
        "total": total,
    }


@router.get("/faculty/{faculty_name}/students-uses-adequacy-distribution")
def students_uses_adequacy_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Pie chart for how *students* use AI adequately/inadequately (as perceived by faculty).
    Expects surveys_df["ia_uses_adequacy_student"] already mapped to short English labels:
      "Unsure", "No misuse", "Appropriate use", "Occasional misuse", "Frequent misuse"
    Returns categories in a fixed logical order + counts.
    Optional demographic filters are supported for future use.
    """
    if "ia_uses_adequacy_student" not in surveys_df.columns:
        return {"categories": [], "values": []}

    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Optional filters (kept for consistency with Uses section)
    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    order = [
        "Unsure",
        "No misuse",
        "Appropriate use",
        "Occasional misuse",
        "Frequent misuse",
    ]

    counts_raw = df["ia_uses_adequacy_student"].value_counts(dropna=False).to_dict()
    counts = [int(counts_raw.get(label, 0)) for label in order]

    return {
        "categories": order,
        "values": counts,
        "total": int(sum(counts)),
    }


@router.get("/faculty/{faculty_name}/students-docchange-by-adequacy")
def students_docchange_by_adequacy(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Stacked bar:
      - X bins: ia_uses_adequacy_student labels *present* in this faculty subset
      - Stacks: counts of selected 'ia_uses_docchange_student' options (multi-select)
    Returns:
      {
        "adequacy_bins": [...],
        "series": [{"name": <docchange option>, "values": [.. per bin ..]}],
        "totals_by_bin": [..],
      }
    """
    df = surveys_df.copy()
    df = df[df["faculty_name"] == faculty_name]

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    if df.empty or "ia_uses_adequacy_student" not in df.columns:
        return {"adequacy_bins": [], "series": [], "totals_by_bin": []}

    # Keep only rows that have some adequacy label and at least one doc-change choice
    df = df.copy()
    df["choices"] = df.get("ia_uses_docchange_student_list", None)
    if "choices" not in df.columns:
        # Fallback: split raw string if list column wasn't created (safety)
        def _fallback_split(x):
            if pd.isna(x):
                return []
            parts = [p.strip() for p in str(x).split(";") if p.strip()]
            return parts

        df["choices"] = df.get("ia_uses_docchange_student", pd.Series([pd.NA] * len(df))).apply(_fallback_split)

    df = df[df["ia_uses_adequacy_student"].notna()]
    df = df[df["choices"].apply(lambda xs: bool(xs))]

    if df.empty:
        return {"adequacy_bins": [], "series": [], "totals_by_bin": []}

    # Canonical adequacy order; we’ll include only present bins in this subset
    adequacy_order = ["Unsure", "No misuse", "Appropriate use", "Occasional misuse", "Frequent misuse"]

    # Count (choice -> adequacy -> count)
    from collections import defaultdict, Counter
    counts_by_choice = defaultdict(Counter)

    for _, row in df.iterrows():
        bin_label = str(row["ia_uses_adequacy_student"])
        for choice in row["choices"]:
            counts_by_choice[str(choice)][bin_label] += 1

    # Determine which adequacy bins are actually present (>0 across any choice)
    present_bins = []
    for bin_label in adequacy_order:
        total_here = sum(c[bin_label] for c in counts_by_choice.values())
        if total_here > 0:
            present_bins.append(bin_label)

    if not present_bins:
        return {"adequacy_bins": [], "series": [], "totals_by_bin": []}

    # Choose a sensible series order (stable)
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

    # Build matrix
    series_out = []
    totals_by_bin = []
    for b in present_bins:
        totals_by_bin.append(sum(counts_by_choice[s][b] for s in used_series))

    for s in used_series:
        series_out.append({
            "name": s,
            "values": [int(counts_by_choice[s][b]) for b in present_bins],
        })

    return {
        "adequacy_bins": present_bins,
        "series": series_out,
        "totals_by_bin": totals_by_bin,
    }


def _apply_filters(df: pd.DataFrame,
                   faculty_name: str,
                   gender: Optional[str],
                   experience: Optional[str],
                   profile: Optional[str]) -> pd.DataFrame:
    x = df[df["faculty_name"] == faculty_name].copy()
    if gender and gender != "All":
        x = x[x["gender"] == gender]
    if experience:
        x = x[x["teaching_experience"] == experience]
    if profile:
        x = x[x["ub_profile"] == profile]
    return x


@router.get("/faculty/{faculty_name}/tools-wordcloud-svg")
def tools_wordcloud_svg(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Wordcloud for 'Which AI tools are they naming?'

    Higher contrast version:
      - Bigger separation: gamma ↑
      - Smaller floor: small words still readable (min_font_size), but visibly smaller
      - Larger cap: let biggest words actually get bigger without breaking layout
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    freq_df = count_tools(df, source_col="ia_uses_tools", unique_per_respondent=True)
    if freq_df.empty:
        svg = (
            "<svg style='max-width:100%;height:280px' viewBox='0 0 1000 280' "
            "xmlns='http://www.w3.org/2000/svg'>"
            "<rect width='100%' height='100%' fill='white'/>"
            "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
            "fill='#6b21a8' font-size='20'>No data for the selected filters.</text>"
            "</svg>"
        )
        return Response(content=svg, media_type="image/svg+xml")

    counts = dict(zip(freq_df["tool"], freq_df["count"]))
    vals = np.array(list(counts.values()), dtype=float)
    vmin, vmax = float(vals.min()), float(vals.max())

    # ----- CONTRAST MAPPING (stronger separation) --------------------------
    # Tune these 3 knobs if you want more/less contrast later:
    gamma = 2.5  # ↑ makes big terms grow faster (more contrast than 1.25)
    floor = 0.22  # ↓ lets small words be smaller, but min_font_size keeps them readable
    cap = 130  # ↑ allows biggest words to be larger (within canvas constraints)
    # -------------------------------.2----------------------------------------

    if vmax == vmin:
        weights = {k: 1.0 for k in counts}
    else:
        weights = {}
        for k, v in counts.items():
            z = (float(v) - vmin) / (vmax - vmin)  # 0..1
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
        scale=1,  # keep =1 to avoid odd SVG scaling
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=purples_trunc,
        min_font_size=10,  # readability floor
        max_font_size=cap,  # larger cap to let big terms pop
        font_step=1,
        random_state=41,
    ).generate_from_frequencies(weights)

    svg = wc.to_svg(embed_font=True)
    svg = svg.replace("<svg ", "<svg style='max-width:100%;height:auto;display:block' ")
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s}"
        "text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}"
        "</style></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/tools-wordcount")
def tools_wordcount(
        faculty_name: str,
        tool: str = Query(..., description="Canonical tool label as rendered in the wordcloud"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)
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


# PERCEPTIONS
@router.get("/faculty/{faculty_name}/perceptions-priorities")
def perceptions_priorities(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

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

    return {
        "axis": axis,  # short axis labels in stable order
        "counts": counts,  # raw counts
        "total": total,  # total selections counted
        "long_map": percep_priorities_long_en,  # for nicer hover on FE
    }


@router.get("/faculty/{faculty_name}/perceptions-students-uses-distribution")
def perceptions_students_uses_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    cats_short: List[str] = [per_students_use_axis_short_en[c] for c in per_students_use_cols]
    cats_long_map: Dict[str, str] = {
        per_students_use_axis_short_en[c]: per_students_use_axis_long_en[c]
        for c in per_students_use_cols
    }

    # Build counts matrix: levels × categories
    series = []
    totals_by_cat = []
    # Precompute totals per category (valid answers)
    for col in per_students_use_cols:
        col_vals = df[col].dropna()
        totals_by_cat.append(int(col_vals.shape[0]))

    for level in LEVELS_ORDER:
        row_counts = []
        for col in per_students_use_cols:
            cnt = int((df[col] == level).sum())
            row_counts.append(cnt)
        series.append({"name": level, "values": row_counts})

    return {
        "categories": cats_short,  # order aligned to per_students_use_cols
        "levels": LEVELS_ORDER,  # order for stacking
        "series": series,  # [{name, values[cat]}...]
        "totals_by_cat": totals_by_cat,
        "long_labels": cats_long_map,  # short -> long (for hover)
    }


@router.get("/faculty/{faculty_name}/perceptions-students-attitudes-distribution")
def perceptions_students_attitudes_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Distribution of agreement levels (Strongly disagree → Strongly agree)
    across the 'students & AI' perception statements.
    Returns 100% stacked bar input: categories (short), levels, series, totals_by_cat, long_labels.
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    if df.empty:
        return {
            "categories": [],
            "levels": [],
            "series": [],
            "totals_by_cat": [],
            "long_labels": {},
        }

    # Stable level order
    levels = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]

    # Compute counts per column/category
    categories = []
    totals_by_cat = []
    counts_per_level = {lvl: [] for lvl in levels}

    for col in per_students_attitudes_cols:
        if col not in df.columns:
            # keep shape consistent
            categories.append(per_students_attitudes_short_en.get(col, col))
            totals_by_cat.append(0)
            for lvl in levels:
                counts_per_level[lvl].append(0)
            continue

        s = df[col].dropna().astype(str)
        # Count each level
        total = 0
        for lvl in levels:
            c = int((s == lvl).sum())
            counts_per_level[lvl].append(c)
            total += c

        categories.append(per_students_attitudes_short_en.get(col, col))
        totals_by_cat.append(total)

    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in levels]
    long_map = {per_students_attitudes_short_en[k]: v for k, v in per_students_attitudes_long_en.items()
                if k in per_students_attitudes_short_en}

    return {
        "categories": categories,
        "levels": levels,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": long_map,
    }


@router.get("/faculty/{faculty_name}/perceptions-tasks-support-distribution")
def perceptions_tasks_support_distribution(
        faculty_name: str,
        domain: str = Query("teaching", regex="^(teaching|research)$"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Pie distribution for:
      - domain='teaching'  -> per_ia_tasks_doc
      - domain='research'  -> per_ia_tasks_rec
    Values are the 4-point agreement scale mapped to English labels.
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    col = "per_ia_tasks_doc" if domain == "teaching" else "per_ia_tasks_rec"
    if col not in df.columns:
        return {"categories": [], "values": [], "domain": domain, "total": 0}

    vc = df[col].value_counts(dropna=True).to_dict()  # already English labels via loader mapping

    categories = []
    values = []
    total = 0
    for lab in LEVEL_ORDER:
        v = int(vc.get(lab, 0))
        categories.append(lab)
        values.append(v)
        total += v

    return {
        "categories": categories,
        "values": values,
        "domain": "Teaching tasks" if domain == "teaching" else "Research tasks",
        "total": total,
    }


@router.get("/faculty/{faculty_name}/perceptions-prof-attitude")
def perceptions_prof_attitude(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Spider (radar) data: professor stance towards AI in teaching–learning.
    Returns counts by label in a fixed axis order for clean plotting.
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    # Column should have been normalized in data_loader -> 'per_prof_attitude'
    col = "PER_IA_POSICPROF_PROH_EV_SUP_INT"
    if col not in df.columns:
        return {
            "axis": [],
            "counts": [],
            "total": 0,
            "long_map": {},
        }

    vc = df[col].value_counts(dropna=True).to_dict()
    counts = [int(vc.get(lbl, 0)) for lbl in PROF_ATT_ORDER]
    total = int(sum(counts))

    # Long labels; fall back to short if not exported
    try:
        long_map = {k: PER_PROF_ATT_LONG_EN.get(k, k) for k in PROF_ATT_ORDER}
    except NameError:
        long_map = {
            "Prohibit": "Prohibit AI in teaching–learning",
            "Avoid": "Avoid AI in teaching–learning",
            "Overcome": "Overcome/mitigate AI use",
            "Integrate": "Integrate AI into pedagogy",
        }

    return {
        "axis": PROF_ATT_ORDER,
        "counts": counts,
        "total": total,
        "long_map": long_map,
    }


@router.get("/faculty/{faculty_name}/perceptions-opportunities-risks-distribution")
def perceptions_opportunities_risks_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    100% stacked vertical bar:
      X = statements (short axis labels)
      stacks = 4-point agreement levels
      hover = long English statement + counts + shares
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    # Keep only the columns that exist
    cols_present = [c for c in PER_OPORISCUNI_COLS if c in df.columns]
    if not cols_present:
        return {
            "categories": [],
            "levels": AGREEMENT4_LEVELS,
            "series": [],
            "totals_by_cat": [],
            "long_labels": {},
        }

    # Prepare axis labels (short) and long map (short -> long)
    categories_short = [PER_OPORISCUNI_AXIS_SHORT_EN.get(c, c) for c in cols_present]
    long_map: Dict[str, str] = {
        PER_OPORISCUNI_AXIS_SHORT_EN.get(c, c): PER_OPORISCUNI_AXIS_LONG_EN.get(c, c)
        for c in cols_present
    }

    # Count per level for each column
    # series[level_index] -> values aligned with categories_short
    counts_per_level: Dict[str, List[int]] = {lvl: [] for lvl in AGREEMENT4_LEVELS}
    totals_by_cat: List[int] = []

    for c in cols_present:
        vc = df[c].value_counts(dropna=True).to_dict()
        total_c = sum(int(vc.get(lvl, 0)) for lvl in AGREEMENT4_LEVELS)
        totals_by_cat.append(int(total_c))
        for lvl in AGREEMENT4_LEVELS:
            counts_per_level[lvl].append(int(vc.get(lvl, 0)))

    series = [
        {"name": lvl, "values": counts_per_level[lvl]}
        for lvl in AGREEMENT4_LEVELS
    ]

    return {
        "categories": categories_short,
        "levels": AGREEMENT4_LEVELS,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": long_map,
    }


@router.get("/faculty/{faculty_name}/training-received-spider")
def training_received_spider(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Spider chart data for: 'Have you received any AI training for teaching or research?'
    Multi-select, ';'-separated in CSV; we count unique selections across respondents.
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    # Count occurrences across the list column
    counts_map: Dict[str, int] = {k: 0 for k in TRAINING_RECEIVED_AXIS}

    if "training_received_list" not in df.columns or df.empty:
        return {
            "axis": TRAINING_RECEIVED_AXIS,
            "counts": [0] * len(TRAINING_RECEIVED_AXIS),
            "total": int(df.shape[0]),
            "long_map": training_received_long_en,
        }

    for lst in df["training_received_list"]:
        if not isinstance(lst, list):
            continue
        for item in lst:
            if item in counts_map:
                counts_map[item] += 1

    counts = [int(counts_map[k]) for k in TRAINING_RECEIVED_AXIS]
    return {
        "axis": TRAINING_RECEIVED_AXIS,
        "counts": counts,
        "total": int(df.shape[0]),
        "long_map": training_received_long_en,
    }


def compute_training_interest_distribution(
        faculty_name: str,
        gender: Optional[str] = None,
        experience: Optional[str] = None,
        profile: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns a pie distribution for FOR_IA_INTERES (0..3 → 4 bins).
    Applies optional demographic filters.
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    col = "FOR_IA_INTERES"
    if col not in df.columns:
        return {"categories": [], "values": [], "total": 0}

    # Safe numeric cast (supports stringified ints)
    s = pd.to_numeric(df[col], errors="coerce").dropna().astype("Int64")

    # Map 0..3 → EN labels, drop anything out of range
    labels = s.map(TRAINING_INTEREST_MAP).dropna()

    counts = labels.value_counts().reindex(TRAINING_INTEREST_ORDER, fill_value=0)
    total = int(counts.sum())

    return {
        "categories": counts.index.tolist(),
        "values": counts.values.tolist(),
        "total": total,
    }


@router.get("/faculty/{faculty}/training-interest-distribution")
def training_interest_distribution(
        faculty: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    return compute_training_interest_distribution(
        faculty_name=faculty,
        gender=gender,
        experience=experience,
        profile=profile,
    )


@router.get("/faculty/{faculty_name}/training-needs-distribution")
def training_needs_distribution(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    100% stacked vertical bar:
      X = ["Teaching","Assessment","Materials","Research"]
      Stacks = ["Strongly disagree","Disagree","Agree","Strongly agree"]
      Values = raw counts (barnorm='percent')
    """
    df = _apply_filters(surveys_df, faculty_name, gender, experience, profile)

    cols_present = [c for c in TRAINING_NEEDS_COLS if c in df.columns]
    if not cols_present or df.empty:
        return {
            "categories": [],
            "levels": AGREEMENT4_LEVELS,
            "series": [],
            "totals_by_cat": [],
            "long_labels": {},
        }

    cats_short = [TRAINING_NEEDS_AXIS_SHORT_EN.get(c, c) for c in cols_present]
    long_map = {
        TRAINING_NEEDS_AXIS_SHORT_EN.get(c, c): TRAINING_NEEDS_AXIS_LONG_EN.get(c, c)
        for c in cols_present
    }

    counts_per_level = {lvl: [] for lvl in AGREEMENT4_LEVELS}
    totals_by_cat = []

    for c in cols_present:
        vc = df[c].value_counts(dropna=True).to_dict()
        total_c = sum(int(vc.get(lvl, 0)) for lvl in AGREEMENT4_LEVELS)
        totals_by_cat.append(int(total_c))
        for lvl in AGREEMENT4_LEVELS:
            counts_per_level[lvl].append(int(vc.get(lvl, 0)))

    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in AGREEMENT4_LEVELS]

    return {
        "categories": cats_short,
        "levels": AGREEMENT4_LEVELS,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": long_map,
    }

@router.get("/open_text/perceptions/opportunities")
def open_text_perceptions_opportunities(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)")
) -> Dict[str, Any]:
    # PER_IA_OPORISCUNI_ALTRES
    return _open_text_aggregates("per_ia_oporiscuni_altres", faculty)


@router.get("/open_text/perceptions/positioning")
def open_text_perceptions_positioning(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)")
) -> Dict[str, Any]:
    # PER_IA_POSICPROF_PERQUE
    return _open_text_aggregates("per_ia_posicprof_perque", faculty)


@router.get("/open_text/training/other_needs")
def open_text_training_other_needs(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)")
) -> Dict[str, Any]:
    # FOR_IA_NECEFORMAT_ALTRES
    return _open_text_aggregates("for_ia_neceformat_altres", faculty)


@router.get("/open_text/comments")
def open_text_general_comments(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)")
) -> Dict[str, Any]:
    # COMENTARIS
    return _open_text_aggregates("comments", faculty)
