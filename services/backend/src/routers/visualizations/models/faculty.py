from typing import List, Optional
from pydantic import BaseModel


class FacultyScoresResponse(BaseModel):
    faculty_name: str
    color: Optional[str] = None
    knowledge_score: float = 0.0
    uses_score: float = 0.0
    perceptions_score: float = 0.0
    training_needs_score: float = 0.0
    total_score: float = 0.0


class TreemapRow(BaseModel):
    faculty_name: str
    label: str
    value: float = 0.0
    overall_faculty_score: float = 0.0
    short_name: str
    color: Optional[str] = None
    color_rgb: Optional[List[int]] = None


class SpikeMapRow(BaseModel):
    faculty_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    color: Optional[str] = None
    short_name: Optional[str] = None
    color_rgb: Optional[List[int]] = None

    category_score: Optional[float] = None
    knowledge_score: Optional[float] = None
    uses_score: Optional[float] = None
    perceptions_score: Optional[float] = None
    training_needs_score: Optional[float] = None

    n_responses: int = 0
