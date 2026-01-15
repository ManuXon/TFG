from __future__ import annotations

import math
from typing import Optional, List, Union

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query, Response

from ..constants import KNOW_APP_COLS, KNOW_APP_MAP_1TO4, KNOW_NAME_MAP
from ..filters import _df_faculty, _filtered_copy, _filtered_view
from ..datastore import STORE
from ..wordclouds import _cache_key, cached_knowledge_wordcloud_svg

from ..models.common import DemographicDistributionSingle, DemographicDistributionDual, LabelLevelsCounts
from ..models.knowledge import KnowledgeFunctionalityCorrelationRow

router = APIRouter()


KNOW_NICE_NAMES = {
    "ia_knowledge_text_creation": "Text Creation",
    "ia_knowledge_multimedia_creation": "Multimedia Creation",
    "ia_knowledge_class_planning": "Class Planning",
    "ia_knowledge_material_design": "Material Design",
    "ia_knowledge_activity_design": "Activity Design",
    "ia_knowledge_evaluation": "Evaluation",
    "ia_knowledge_research_management": "Research Management",
    "ia_knowledge_data_collection": "Data Collection",
    "ia_knowledge_transcription_translation": "Transcription / Translation",
    "ia_knowledge_data_analysis": "Data Analysis",
    "ia_knowledge_technical_support": "Technical Support",
    "ia_knowledge_ai_experiments": "AI Experiments",
    "ia_knowledge_inclusion_support": "Inclusion Support",
}


@router.get("/faculty/{faculty_name}/knowledge-distribution", response_model=Union[DemographicDistributionSingle, DemographicDistributionDual])
def knowledge_distribution(
    faculty_name: str,
    demographic1: str = "gender",
    demographic2: Optional[str] = None,
):
    df = _df_faculty(STORE.surveys(), faculty_name).copy()

    knowledge_map = {"No knowledge": 1, "Little knowledge": 2, "Good knowledge": 3, "Expert knowledge": 4}
    if "ia_knowledge" not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    df["knowledge_num"] = pd.to_numeric(df["ia_knowledge"].map(knowledge_map), errors="coerce")

    col_map = {"gender": "gender", "experience": "teaching_experience", "profile": "ub_profile"}
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    if col1 not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

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

    g["contribution"] = np.where(
        g["n_main"].astype(float) > 0,
        (g["mean_sub"].astype(float) * g["n_sub"].astype(float)) / g["n_main"].astype(float),
        0.0,
    )

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


@router.get(
    "/faculty/{faculty_name}/knowledge-functionality-correlation",
    response_model=List[KnowledgeFunctionalityCorrelationRow],
)
def knowledge_functionality_correlation(
    faculty_name: str,
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    needed = ["ia_knowledge", *KNOW_APP_COLS]
    df = _filtered_copy(faculty_name, gender, experience, profile, cols=needed)
    if df.empty:
        return []

    if "ia_knowledge" not in df.columns:
        return []

    missing = [c for c in KNOW_APP_COLS if c not in df.columns]
    if missing:
        return []

    # Robust mapping:
    # - if column already numeric, keep numeric
    # - else map strings -> 1..4
    # - clamp to [1, 4] to kill garbage
    for col in KNOW_APP_COLS:
        s = df[col]

        if pd.api.types.is_numeric_dtype(s):
            mapped = pd.to_numeric(s, errors="coerce")
        else:
            mapped = (
                s.astype(str)
                .str.strip()
                .map(KNOW_APP_MAP_1TO4)
            )
            mapped = pd.to_numeric(mapped, errors="coerce")

        # clamp to valid range
        mapped = mapped.where(mapped.between(1.0, 4.0))
        df[col] = mapped

    # Grouping label must exist
    df = df.dropna(subset=["ia_knowledge"])
    if df.empty:
        return []

    means = (
        df.groupby("ia_knowledge", observed=True)[KNOW_APP_COLS]
        .mean(numeric_only=True)
        .rename(columns=KNOW_NICE_NAMES)
    )

    n_by_group = df.groupby("ia_knowledge", observed=True).size()
    total_n = float(n_by_group.sum()) or 1.0

    summary = pd.DataFrame(index=means.index)
    summary["knowledge_label"] = summary.index
    summary["n"] = n_by_group.astype(int)
    summary["pct"] = (n_by_group / total_n) * 100.0
    summary["group_mean"] = means.mean(axis=1)
    summary["group_min"] = means.min(axis=1)
    summary["group_max"] = means.max(axis=1)

    result_df = pd.concat([summary, means], axis=1).reset_index(drop=True)
    result_df = result_df.replace([float("inf"), float("-inf")], None).fillna(0)

    return result_df.to_dict(orient="records")


@router.get("/faculty/{faculty_name}/knowledge-applications-wordcloud-svg")
def knowledge_applications_wordcloud_svg(
    faculty_name: str,
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    svg = cached_knowledge_wordcloud_svg(_cache_key(faculty_name, gender, experience, profile))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/knowledge-applications-distribution-count",
            response_model=LabelLevelsCounts
            )
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
        return {"label": app_label, "levels": list(KNOW_APP_MAP_1TO4.keys()), "counts": {}, "total": 0}
    if col not in df.columns:
        return {"label": app_label, "levels": list(KNOW_APP_MAP_1TO4.keys()), "counts": {}, "total": 0}

    levels = ["I don't know any", "I know a few", "I know several", "I know many"]
    counts = {lvl: int((df[col] == lvl).sum()) for lvl in levels}
    total = int(sum(counts.values()))
    return {"label": app_label, "levels": levels, "counts": counts, "total": total}
