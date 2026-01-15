from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query, Response

from ..constants import (
    USES_FREQ_MAP_1TO4,
    USES_NAME_MAP,
    USES_TASK_COLS,
    USES_STUDENT_TASK_COLS,
)
from ..filters import _df_faculty, _filtered_copy, _filtered_view
from ..datastore import STORE
from ..wordclouds import _cache_key, cached_uses_wordcloud_svg

from ..models.common import DemographicDistributionSingle, DemographicDistributionDual, CategoriesValuesInt, LabelLevelsCounts
from ..models.uses import (
    UsesFunctionalityCorrelationRow,
    StudentsUsesByProposalRow,
    StudentsUsesAdequacyDistributionResponse,
    StudentsDocchangeByAdequacyResponse,
)

router = APIRouter()

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


@router.get("/faculty/{faculty_name}/uses-distribution", response_model=Union[DemographicDistributionSingle, DemographicDistributionDual])
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

    if col2 not in df.columns:
        return {"mode": "single", "demographics": [demographic1], "categories": [], "values": []}

    g = (
        df.groupby([col1, col2], observed=True)["uses_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    g["n_main"] = g.groupby("main", observed=True)["n_sub"].transform("sum")
    main_avg_map = df.groupby(col1, observed=True)["uses_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    g["contribution"] = np.where(
        g["n_main"].astype(float) > 0,
        (g["mean_sub"].astype(float) * g["n_sub"].astype(float)) / g["n_main"].astype(float),
        0.0,
    )

    num_cols = ["mean_sub", "n_sub", "n_main", "main_avg", "contribution"]
    g[num_cols] = g[num_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]].to_dict(orient="records"),
    }


@router.get("/faculty/{faculty_name}/proposes-distribution", response_model=CategoriesValuesInt)
def proposes_distribution(faculty_name: str):
    df = _df_faculty(STORE.surveys(), faculty_name)
    column = "ia_proposes_students"
    order = ["Never", "Sometimes", "Often", "Very often"]
    if column not in df.columns:
        return {"categories": order, "values": [0, 0, 0, 0]}
    counts_raw = df[column].value_counts().to_dict()
    counts = [int(counts_raw.get(level, 0)) for level in order]
    return {"categories": order, "values": counts}


@router.get("/faculty/{faculty_name}/uses-functionality-correlation",
            response_model=List[UsesFunctionalityCorrelationRow]
            )
def uses_functionality_correlation(
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


@router.get("/faculty/{faculty_name}/students-uses-by-proposal", response_model=List[StudentsUsesByProposalRow])
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
    svg = cached_uses_wordcloud_svg(_cache_key(faculty_name, gender, experience, profile))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/uses-applications-distribution-count",
            response_model=LabelLevelsCounts
            )
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
    if not col or col not in df.columns:
        return {"label": app_label, "levels": ["Never", "Sometimes", "Often", "Very often"], "counts": {}, "total": 0}

    levels = ["Never", "Sometimes", "Often", "Very often"]
    raw = df[col].value_counts().to_dict()
    counts = {lvl: int(raw.get(lvl, 0)) for lvl in levels}
    total = int(sum(counts.values()))
    return {"label": app_label, "levels": levels, "counts": counts, "total": total}


@router.get("/faculty/{faculty_name}/students-uses-adequacy-distribution", response_model=StudentsUsesAdequacyDistributionResponse)
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


@router.get("/faculty/{faculty_name}/students-docchange-by-adequacy", response_model=StudentsDocchangeByAdequacyResponse)
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
        raw = df["ia_uses_docchange_student"] if "ia_uses_docchange_student" in df.columns else pd.Series([pd.NA] * len(df))

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
