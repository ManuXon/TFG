from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.utils.data_loader import (
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
)

from ..constants import AGREE4_ORDER, LEVELS_ORDER, PROF_ATT_ORDER
from ..filters import _df_faculty, _filtered_view
from ..datastore import STORE
from ..models.common import AxisCountsWithTotal, CategoriesValuesInt, StackedDistribution
from ..models.perceptions import TasksSupportDistributionResponse


router = APIRouter()


@router.get("/faculty/{faculty_name}/normative-distribution", response_model=CategoriesValuesInt)
def normative_distribution(faculty_name: str):
    df = _df_faculty(STORE.surveys(), faculty_name)
    column = "ia_normative_ub"
    if column not in df.columns:
        return {"categories": [], "values": []}
    distribution = df[column].value_counts().to_dict()
    return {"categories": list(distribution.keys()), "values": list(distribution.values())}


@router.get("/faculty/{faculty_name}/perceptions-priorities", response_model=AxisCountsWithTotal)
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


@router.get("/faculty/{faculty_name}/perceptions-students-uses-distribution", response_model=StackedDistribution)
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


@router.get("/faculty/{faculty_name}/perceptions-students-attitudes-distribution", response_model=StackedDistribution)
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
    long_map = {
        per_students_attitudes_short_en[k]: v
        for k, v in per_students_attitudes_long_en.items()
        if k in per_students_attitudes_short_en
    }

    return {
        "categories": categories,
        "levels": levels,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": long_map,
    }


@router.get("/faculty/{faculty_name}/perceptions-tasks-support-distribution", response_model=TasksSupportDistributionResponse)
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

    return {
        "categories": categories,
        "values": values,
        "domain": "Teaching tasks" if domain == "teaching" else "Research tasks",
        "total": total,
    }


@router.get("/faculty/{faculty_name}/perceptions-prof-attitude", response_model=AxisCountsWithTotal)
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

    long_map = {k: per_prof_attitude_long_en.get(k, k) for k in PROF_ATT_ORDER}
    return {"axis": PROF_ATT_ORDER, "counts": counts, "total": total, "long_map": long_map}


@router.get("/faculty/{faculty_name}/perceptions-opportunities-risks-distribution", response_model=StackedDistribution)
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
    return {
        "categories": categories_short,
        "levels": AGREEMENT4_LEVELS,
        "series": series,
        "totals_by_cat": totals_by_cat,
        "long_labels": long_map,
    }
