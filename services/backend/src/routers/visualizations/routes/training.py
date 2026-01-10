from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Query

from src.utils.data_loader import (
    AGREEMENT4_LEVELS,
    TRAINING_RECEIVED_AXIS,
    training_received_long_en,
    TRAINING_INTEREST_MAP,
    TRAINING_INTEREST_ORDER,
    TRAINING_NEEDS_COLS,
    TRAINING_NEEDS_AXIS_SHORT_EN,
    TRAINING_NEEDS_AXIS_LONG_EN,
)

from ..filters import _filtered_view
from ..models.common import AxisCountsWithTotal, StackedDistribution
from ..models.training import TrainingInterestDistributionResponse


router = APIRouter()


@router.get("/faculty/{faculty_name}/training-received-spider", response_model=AxisCountsWithTotal)
def training_received_spider(
    faculty_name: str,
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)

    counts_map: Dict[str, int] = {k: 0 for k in TRAINING_RECEIVED_AXIS}
    if "training_received_list" not in df.columns or df.empty:
        return {
            "axis": TRAINING_RECEIVED_AXIS,
            "counts": [0] * len(TRAINING_RECEIVED_AXIS),
            "total": int(df.shape[0]),
            "long_map": training_received_long_en,
        }

    for lst in df["training_received_list"]:
        if isinstance(lst, list):
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
    df = _filtered_view(faculty_name, gender, experience, profile)
    col = "FOR_IA_INTERES"
    if col not in df.columns:
        return {"categories": [], "values": [], "total": 0}

    s = pd.to_numeric(df[col], errors="coerce").dropna().astype("Int64")
    labels = s.map(TRAINING_INTEREST_MAP).dropna()

    counts = labels.value_counts().reindex(TRAINING_INTEREST_ORDER, fill_value=0)
    total = int(counts.sum())
    return {"categories": counts.index.tolist(), "values": counts.values.tolist(), "total": total}


@router.get("/faculty/{faculty}/training-interest-distribution", response_model=TrainingInterestDistributionResponse)
def training_interest_distribution(
    faculty: str,
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    return compute_training_interest_distribution(faculty_name=faculty, gender=gender, experience=experience, profile=profile)


@router.get("/faculty/{faculty_name}/training-needs-distribution", response_model=StackedDistribution)
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
    return {
        "categories": cats_short,
        "levels": AGREEMENT4_LEVELS,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": long_map,
    }
