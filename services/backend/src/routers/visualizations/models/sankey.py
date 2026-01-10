from typing import Dict, List
from pydantic import BaseModel, Field


class SankeyDataResponse(BaseModel):
    sources: List[int] = Field(default_factory=list)
    targets: List[int] = Field(default_factory=list)
    values: List[float] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    faculty_colors: Dict[str, str] = Field(default_factory=dict)
