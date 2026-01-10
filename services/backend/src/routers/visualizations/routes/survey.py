from __future__ import annotations

from typing import Any, Dict, Literal, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from ..constants import (
    EXPERIENCE_ORDER,
    GENDER_ORDER,
    MODE_ORDER,
    PROFILE_ORDER,
)
from ..datastore import STORE
from ..filters import _df_faculty

from ..models.common import CategoriesCounts
from ..models.survey import SurveySummaryResponse, SurveyFacultiesResponse

router = APIRouter()


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


@router.get("/survey/summary", response_model=SurveySummaryResponse)
def survey_summary(
        faculty: Optional[str] = Query(None, description="Optional faculty name (short EN) to filter responses"),
) -> Dict[str, Any]:
    df = _df_faculty(STORE.surveys(), faculty)
    total_responses = int(len(df))
    total_faculties = int(STORE.surveys().get("faculty_name", pd.Series(dtype=str)).nunique())
    return {"total_responses": total_responses, "total_faculties": total_faculties}


@router.get("/survey/distribution", response_model=CategoriesCounts)
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


@router.get("/survey/faculties", response_model=SurveyFacultiesResponse)
def survey_faculties(min_count: int = 1) -> Dict[str, Any]:
    df = STORE.surveys()
    if df.empty or "faculty_name" not in df.columns:
        return {"faculties": [], "total": 0}

    vc = df["faculty_name"].dropna().astype(str).value_counts().sort_index()
    rows = [{"faculty_name": name, "responses": int(count)} for name, count in vc.items() if
            int(count) >= int(min_count)]
    return {"faculties": rows, "total": int(sum(r["responses"] for r in rows))}
