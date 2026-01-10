from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from wordcloud import WordCloud

from src.utils.tools_normalizer import count_tools

from .colormaps import purples_trunc, reds_trunc
from .constants import KNOW_APP_MAP_1TO4, KNOW_NAME_MAP, USES_FREQ_MAP_1TO4, USES_NAME_MAP
from .filters import _filtered_copy, _filtered_view
from .normalize import _norm_demo, _norm_faculty


def _empty_svg(message: str) -> str:
    return (
        "<svg style='max-width:100%;height:280px' viewBox='0 0 1000 280' "
        "xmlns='http://www.w3.org/2000/svg'>"
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
        f"fill='#6b21a8' font-size='20'>{message}</text>"
        "</svg>"
    )


def _cache_key(
    faculty: str,
    gender: Optional[str],
    experience: Optional[str],
    profile: Optional[str],
) -> Tuple[str, str, str, str]:
    return (_norm_faculty(faculty), _norm_demo(gender), _norm_demo(experience), _norm_demo(profile))


def _finalize_wc_svg(svg: str) -> str:
    svg = svg.replace("<svg ", "<svg style='max-width:100%;height:auto;display:block' ")
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s}"
        "text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}"
        "</style></svg>",
    )
    return svg


@lru_cache(maxsize=512)
def cached_knowledge_wordcloud_svg(key: Tuple[str, str, str, str]) -> str:
    faculty_key, gender, exp, prof = key
    df = _filtered_copy(faculty_key, gender, exp, prof, cols=list(KNOW_NAME_MAP.keys()))
    if df.empty:
        return _empty_svg("No data for the selected filters.")

    missing = [c for c in KNOW_NAME_MAP.keys() if c not in df.columns]
    if missing:
        return _empty_svg("No data available (missing columns).")

    for col in KNOW_NAME_MAP.keys():
        df[col] = df[col].map(KNOW_APP_MAP_1TO4).fillna(0.0)

    total_scores = df[list(KNOW_NAME_MAP.keys())].sum().to_dict()
    gamma = 1.25
    freqs = {KNOW_NAME_MAP[c]: float(v) ** gamma for c, v in total_scores.items()}

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=50,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=reds_trunc,
    ).generate_from_frequencies(freqs)

    return _finalize_wc_svg(wc.to_svg(embed_font=True))


@lru_cache(maxsize=512)
def cached_uses_wordcloud_svg(key: Tuple[str, str, str, str]) -> str:
    faculty_key, gender, exp, prof = key
    df = _filtered_copy(faculty_key, gender, exp, prof, cols=list(USES_NAME_MAP.keys()))
    if df.empty:
        return _empty_svg("No data for the selected filters.")

    missing = [c for c in USES_NAME_MAP.keys() if c not in df.columns]
    if missing:
        return _empty_svg("No data available (missing columns).")

    for col in USES_NAME_MAP.keys():
        df[col] = df[col].map(USES_FREQ_MAP_1TO4).fillna(0.0)

    total_scores = df[list(USES_NAME_MAP.keys())].sum().to_dict()
    gamma = 1.25
    freqs = {USES_NAME_MAP[c]: float(v) ** gamma for c, v in total_scores.items()}

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=50,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=purples_trunc,
    ).generate_from_frequencies(freqs)

    return _finalize_wc_svg(wc.to_svg(embed_font=True))


@lru_cache(maxsize=512)
def cached_tools_wordcloud_svg(key: Tuple[str, str, str, str]) -> str:
    faculty_key, gender, exp, prof = key
    df = _filtered_view(faculty_key, gender, exp, prof)
    freq_df = count_tools(df, source_col="ia_uses_tools", unique_per_respondent=True)
    if freq_df.empty:
        return _empty_svg("No data for the selected filters.")

    counts = dict(zip(freq_df["tool"], freq_df["count"]))
    vals = np.array(list(counts.values()), dtype=float)
    vmin, vmax = float(vals.min()), float(vals.max())

    gamma = 2.5
    floor = 0.22
    cap = 130

    if vmax == vmin:
        weights = {k: 1.0 for k in counts}
    else:
        weights: Dict[str, float] = {}
        for k, v in counts.items():
            z = (float(v) - vmin) / (vmax - vmin)
            w = floor + (1.0 - floor) * (z ** gamma)
            weights[k] = float(w)

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=80,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=purples_trunc,
        min_font_size=10,
        max_font_size=cap,
        font_step=1,
        random_state=41,
    ).generate_from_frequencies(weights)

    return _finalize_wc_svg(wc.to_svg(embed_font=True))
