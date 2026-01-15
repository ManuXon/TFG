from typing import List
from pydantic import BaseModel, Field


class TasksSupportDistributionResponse(BaseModel):
    categories: List[str] = Field(default_factory=list)
    values: List[int] = Field(default_factory=list)
    domain: str
    total: int = 0
