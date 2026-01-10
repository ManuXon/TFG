from __future__ import annotations

from typing import List, Optional

import pandas as pd

from .constants import FACULTY_KEY_COL
from .datastore import STORE
from .normalize import _norm_faculty, _norm_demo


def _df_faculty(df: pd.DataFrame, faculty: Optional[str]) -> pd.DataFrame:
    if not faculty:
        return df
    key = _norm_faculty(faculty)

    if FACULTY_KEY_COL in df.columns:
        return df[df[FACULTY_KEY_COL] == key]

    if "faculty_name" not in df.columns:
        return df.iloc[0:0]

    return df[df["faculty_name"].astype(str).str.strip().str.lower() == key]


def _apply_demo_filters(
    df: pd.DataFrame,
    gender: Optional[str],
    experience: Optional[str],
    profile: Optional[str],
) -> pd.DataFrame:
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


def _filtered_view(
    faculty: Optional[str],
    gender: Optional[str],
    experience: Optional[str],
    profile: Optional[str],
) -> pd.DataFrame:
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
    fdf = STORE.faculties()
    if fdf.empty:
        return pd.DataFrame(columns=["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb", FACULTY_KEY_COL])
    return fdf.copy()
