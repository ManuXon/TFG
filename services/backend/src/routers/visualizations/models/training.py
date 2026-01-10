from typing import List
from pydantic import BaseModel, Field


class TrainingInterestDistributionResponse(BaseModel):
    categories: List[str] = Field(default_factory=list)
    values: List[int] = Field(default_factory=list)
    total: int = 0
