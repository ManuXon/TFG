from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .constants import SCORE_COLS
from .datastore import STORE
from .filters import _faculty_meta_by_name
from .normalize import _sanitize_num_list


def get_sankey_chart_data() -> Dict[str, Any]:
    df = STORE.surveys()

    needed = ["faculty_name", "gender", "teaching_experience", "ub_profile", *[c for c in SCORE_COLS if c in df.columns]]
    work = df.loc[:, [c for c in needed if c in df.columns]].copy()
    fmeta = _faculty_meta_by_name()

    if "gender" in work.columns:
        work["gender"] = work["gender"].astype(str).where(work["gender"].notna(), "No answer")

    for c in ["teaching_experience", "ub_profile"]:
        if c in work.columns:
            work[c] = work[c].where(pd.notna(work[c]), None)

    genders = [v for v in work.get("gender", pd.Series(dtype=str)).dropna().unique().tolist() if str(v).strip()]
    exps = [v for v in work.get("teaching_experience", pd.Series(dtype=str)).dropna().unique().tolist() if str(v).strip()]
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

    third_layer_indices: Dict[str, int] = {}
    for v in list(map(str, genders)) + list(map(str, exps)) + list(map(str, profiles)):
        if v in label_to_idx:
            third_layer_indices[v] = label_to_idx[v]

    faculty_indices = {str(f): label_to_idx[str(f)] for f in faculties_list if str(f) in label_to_idx}

    sources: List[int] = []
    targets: List[int] = []
    values: List[float] = []

    # score dimension -> demographic block
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

    # demographic block -> subgroup
    score_present = [c for c in SCORE_COLS if c in work.columns]
    if score_present:
        for category, cat_idx in second_layer_indices.items():
            if category not in work.columns:
                continue

            g = work.groupby(category, observed=True)[score_present].sum(numeric_only=True, min_count=1)
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

    # subgroup -> faculty (aggregated)
    if score_present and "faculty_name" in work.columns:
        faculty_score = work[score_present].sum(axis=1, skipna=True)

        long = work[["faculty_name", "gender", "teaching_experience", "ub_profile"]].copy()
        long["faculty_score"] = faculty_score
        long = (
            long.melt(
                id_vars=["faculty_name", "faculty_score"],
                value_vars=["gender", "teaching_experience", "ub_profile"],
                var_name="category",
                value_name="subgroup",
            )
            .dropna(subset=["faculty_name", "subgroup"])
        )

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

    # faculty colors
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
