from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from ..open_text_service import open_text_aggregates, open_text_items
from ..models import OpenTextAggregatesResponse, OpenTextItemsResponse

router = APIRouter()


@router.get("/open_text/perceptions/opportunities", response_model=OpenTextAggregatesResponse)
def open_text_perceptions_opportunities(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_aggregates("per_ia_oporiscuni_altres", faculty)


@router.get("/open_text/perceptions/positioning", response_model=OpenTextAggregatesResponse)
def open_text_perceptions_positioning(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_aggregates("per_ia_posicprof_perque", faculty)


@router.get("/open_text/training/other_needs", response_model=OpenTextAggregatesResponse)
def open_text_training_other_needs(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_aggregates("for_ia_neceformat_altres", faculty)


@router.get("/open_text/comments", response_model=OpenTextAggregatesResponse)
def open_text_general_comments(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_aggregates("comments", faculty)


@router.get("/open_text/perceptions/opportunities/items", response_model=OpenTextItemsResponse)
def open_text_perceptions_opportunities_items(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_items("per_ia_oporiscuni_altres", faculty)


@router.get("/open_text/perceptions/positioning/items", response_model=OpenTextItemsResponse)
def open_text_perceptions_positioning_items(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_items("per_ia_posicprof_perque", faculty)


@router.get("/open_text/training/other_needs/items", response_model=OpenTextItemsResponse)
def open_text_training_other_needs_items(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_items("for_ia_neceformat_altres", faculty)


@router.get("/open_text/comments/items", response_model=OpenTextItemsResponse)
def open_text_general_comments_items(
    faculty: Optional[str] = Query(None, description="Faculty name (short EN)"),
) -> Dict[str, Any]:
    return open_text_items("comments", faculty)
