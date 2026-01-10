from typing import List
from pydantic import BaseModel, Field
from .common import CorrelationRowBase, NamedSeriesInt


class UsesFunctionalityCorrelationRow(CorrelationRowBase):
    usage_label: str


class StudentsUsesByProposalRow(CorrelationRowBase):
    proposal_label: str


class StudentsUsesAdequacyDistributionResponse(BaseModel):
    categories: List[str] = Field(default_factory=list)
    values: List[int] = Field(default_factory=list)
    total: int = 0


class StudentsDocchangeByAdequacyResponse(BaseModel):
    adequacy_bins: List[str] = Field(default_factory=list)
    series: List[NamedSeriesInt] = Field(default_factory=list)
    totals_by_bin: List[int] = Field(default_factory=list)
