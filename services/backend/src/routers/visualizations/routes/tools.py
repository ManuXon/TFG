from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Response

from src.utils.tools_normalizer import count_tools

from ..filters import _filtered_view
from ..wordclouds import _cache_key, cached_tools_wordcloud_svg
from ..models.tools import ToolWordcountResponse

router = APIRouter()


@router.get("/faculty/{faculty_name}/tools-wordcloud-svg")
def tools_wordcloud_svg(
    faculty_name: str,
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    svg = cached_tools_wordcloud_svg(_cache_key(faculty_name, gender, experience, profile))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/tools-wordcount", response_model=ToolWordcountResponse)
def tools_wordcount(
    faculty_name: str,
    tool: str = Query(..., description="Canonical tool label as rendered in the wordcloud"),
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    df = _filtered_view(faculty_name, gender, experience, profile)
    freq_df = count_tools(df, source_col="ia_uses_tools", unique_per_respondent=True)
    total = int(freq_df["count"].sum()) if not freq_df.empty else 0

    if freq_df.empty:
        return {"tool": tool, "count": 0, "total": 0, "share": 0.0}

    row = freq_df[freq_df["tool"] == tool]
    if row.empty:
        return {"tool": tool, "count": 0, "total": total, "share": 0.0}

    count = int(row["count"].iloc[0])
    share = float(row["share"].iloc[0])
    return {"tool": tool, "count": count, "total": total, "share": share}
