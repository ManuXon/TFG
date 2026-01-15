from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from src.utils.data_loader import df_to_json_safe

from ..constants import SCORE_COLS
from ..datastore import STORE
from ..filters import _filtered_view, _faculty_meta_by_name
from ..normalize import _sanitize_float, _norm_faculty

from ..models.faculty import FacultyScoresResponse, TreemapRow, SpikeMapRow
router = APIRouter()
logger = logging.getLogger("uvicorn")


@router.get("/faculty/{faculty_name}/scores", response_model=FacultyScoresResponse)
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
        "color": (str(color) if color is not None else None),
        **metric_means,
        "total_score": float(total_score),
    }


@router.get("/treemap-data", response_model=List[TreemapRow])
def get_treemap_data(
    gender: Optional[str] = None,
    teaching_experience: Optional[str] = None,
    ub_profile: Optional[str] = None,
):
    df = _filtered_view(None, gender, teaching_experience, ub_profile)
    if df.empty:
        return []

    fac_means = (
        df.groupby("faculty_name", observed=True)[SCORE_COLS]
        .mean(numeric_only=True)
        .reset_index()
    )

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


@router.get("/spike-map", response_model=List[SpikeMapRow])
def get_spike_map_data(
    category: str = "All",
    gender: Optional[str] = None,
    teaching_experience: Optional[str] = None,
    ub_profile: Optional[str] = None,
):
    try:
        df = _filtered_view(None, gender, teaching_experience, ub_profile)
        if df.empty or "faculty_name" not in df.columns:
            return df_to_json_safe(
                pd.DataFrame(
                    columns=[
                        "faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb",
                        "category_score", "knowledge_score", "uses_score", "perceptions_score", "training_needs_score",
                        "n_responses",
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
        out = agg.merge(
            meta[["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb"]],
            on="faculty_name",
            how="left",
        )

        out = out.replace([np.inf, -np.inf], np.nan)
        out = out.where(pd.notna(out), None)
        return df_to_json_safe(out)

    except Exception as e:
        logger.exception("Error computing spike-map")
        raise HTTPException(status_code=500, detail=f"Failed to compute spike-map: {type(e).__name__}")
