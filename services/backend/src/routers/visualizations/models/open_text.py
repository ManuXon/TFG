from typing import Dict, List
from pydantic import BaseModel, Field


class LabelsCounts(BaseModel):
    labels: List[str] = Field(default_factory=list)
    counts: List[int] = Field(default_factory=list)


class OpenTextAggregatesResponse(BaseModel):
    sentiment: LabelsCounts = Field(default_factory=LabelsCounts)
    topics: LabelsCounts = Field(default_factory=LabelsCounts)


class OpenTextItem(BaseModel):
    row_id: int = -1
    sentiment: str = "neutral"
    sentiment_fine: str = "neutral"
    cluster_id: int = -1
    cluster_label: str = "Unclassified"
    main_topics: List[str] = Field(default_factory=list)
    english_text: str = ""


class OpenTextItemsResponse(BaseModel):
    items: List[OpenTextItem] = Field(default_factory=list)
