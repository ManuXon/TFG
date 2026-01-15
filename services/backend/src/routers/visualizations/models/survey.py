from typing import List
from pydantic import BaseModel, Field


class SurveySummaryResponse(BaseModel):
    total_responses: int
    total_faculties: int


class FacultyResponsesRow(BaseModel):
    faculty_name: str
    responses: int


class SurveyFacultiesResponse(BaseModel):
    faculties: List[FacultyResponsesRow] = Field(default_factory=list)
    total: int = 0
