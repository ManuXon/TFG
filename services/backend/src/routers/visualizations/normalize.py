from __future__ import annotations

import math
from typing import Any, List, Optional


def _norm_opt(x: Optional[str]) -> str:
    return (x or "").strip()


def _norm_faculty(x: Optional[str]) -> str:
    return _norm_opt(x).lower()


def _norm_demo(x: Optional[str]) -> str:
    v = _norm_opt(x)
    return "" if v in {"", "All"} else v


def _sanitize_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        if not math.isfinite(f):
            return None
        return f
    except Exception:
        return None


def _color_rgb_to_list(v: Any) -> Optional[List[int]]:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None

    if isinstance(v, (list, tuple)) and len(v) == 3:
        try:
            return [int(x) for x in v]
        except Exception:
            return None

    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                import json

                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) == 3:
                    return [int(x) for x in arr]
            except Exception:
                return None

    return None


def _sanitize_num_list(seq: List[Any]) -> List[Any]:
    out: List[Any] = []
    for x in seq:
        # avoid numpy scalar JSON issues without importing numpy here
        try:
            import numpy as np  # local import to keep this module lightweight

            if isinstance(x, (np.integer,)):
                x = int(x)
            elif isinstance(x, (np.floating,)):
                x = float(x)
        except Exception:
            pass

        if isinstance(x, float) and not math.isfinite(x):
            x = 0.0
        out.append(x)
    return out

