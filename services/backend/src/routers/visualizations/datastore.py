from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.utils.data_loader import load_faculties_data, load_surveys_data
from src.utils.open_text_agent import load_open_text_analysis

from .constants import FACULTY_KEY_COL, SCORE_COLS
from .normalize import _color_rgb_to_list


DATA_TTL_SEC = int(os.getenv("DATA_TTL_SEC", "0"))  # 0 = never reload


@dataclass(frozen=True)
class _Meta:
    faculty_name: Optional[str]
    latitude: Any
    longitude: Any
    color: Any
    short_name: Any
    color_rgb: Optional[list[int]]


class DataStore:
    """
    Loads + preprocesses data once per process (gunicorn/uvicorn worker).
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
            out[FACULTY_KEY_COL] = out["faculty_name"].astype(str).str.strip().str.lower()
        else:
            out[FACULTY_KEY_COL] = ""

        for c in ["faculty_name", "gender", "teaching_experience", "ub_profile", "teaching_mode"]:
            if c in out.columns:
                try:
                    out[c] = out[c].astype("category")
                except Exception:
                    pass

        for c in SCORE_COLS:
            if c in out.columns:
                out[c] = pd.to_numeric(out[c], errors="coerce")

        return out

    @staticmethod
    def _prep_faculties(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, _Meta]]:
        out = df.copy()

        if "faculty_name" in out.columns:
            out[FACULTY_KEY_COL] = out["faculty_name"].astype(str).str.strip().str.lower()
        else:
            out[FACULTY_KEY_COL] = ""

        for col in ["latitude", "longitude", "color", "short_name", "color_rgb"]:
            if col not in out.columns:
                out[col] = pd.NA

        out["color_rgb"] = out["color_rgb"].apply(_color_rgb_to_list)

        meta: Dict[str, _Meta] = {}
        for _, r in out.iterrows():
            k = str(r.get(FACULTY_KEY_COL, "") or "")
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

        keep = ["faculty_name", FACULTY_KEY_COL, "latitude", "longitude", "color", "short_name", "color_rgb"]
        return out[keep], meta


STORE = DataStore()
