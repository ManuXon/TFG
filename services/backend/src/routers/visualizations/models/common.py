from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# -------------------------
# Small reusable shapes
# -------------------------

class CategoriesCounts(BaseModel):
    categories: List[str] = Field(default_factory=list)
    counts: List[int] = Field(default_factory=list)


class CategoriesValuesInt(BaseModel):
    categories: List[str] = Field(default_factory=list)
    values: List[int] = Field(default_factory=list)


class CategoriesValuesFloat(BaseModel):
    categories: List[str] = Field(default_factory=list)
    values: List[float] = Field(default_factory=list)


class AxisCountsWithTotal(BaseModel):
    axis: List[str] = Field(default_factory=list)
    counts: List[int] = Field(default_factory=list)
    total: int = 0
    long_map: Dict[str, str] = Field(default_factory=dict)


class LabelLevelsCounts(BaseModel):
    label: str
    levels: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)
    total: int = 0


class NamedSeriesInt(BaseModel):
    name: str
    values: List[int] = Field(default_factory=list)


class StackedDistribution(BaseModel):
    """
    Used by endpoints that return:
    {
      "categories": [...],
      "levels": [...],
      "series": [{"name": level, "values": [...]}, ...],
      "totals_by_cat": [...],
      "long_labels": {...}
    }
    """
    categories: List[str] = Field(default_factory=list)
    levels: List[str] = Field(default_factory=list)
    series: List[NamedSeriesInt] = Field(default_factory=list)
    totals_by_cat: List[int] = Field(default_factory=list)
    long_labels: Dict[str, str] = Field(default_factory=dict)


# -------------------------
# Shared "single vs dual" demographic distribution
# (used by Knowledge + Uses)
# -------------------------

class DualDemographicRow(BaseModel):
    main: str
    sub: str
    mean_sub: float = 0.0
    n_sub: int = 0
    n_main: int = 0
    main_avg: float = 0.0
    contribution: float = 0.0


class DemographicDistributionSingle(BaseModel):
    mode: Literal["single"]
    demographics: List[str]
    categories: List[str] = Field(default_factory=list)
    values: List[float] = Field(default_factory=list)


class DemographicDistributionDual(BaseModel):
    mode: Literal["dual"]
    demographics: List[str]
    data: List[DualDemographicRow] = Field(default_factory=list)


DemographicDistribution = Union[DemographicDistributionSingle, DemographicDistributionDual]


# -------------------------
# Correlation rows with dynamic keys
# (because you emit columns like "Text Creation" with spaces)
# -------------------------

class CorrelationRowBase(BaseModel):
    n: int = 0
    pct: float = 0.0
    group_mean: float = 0.0
    group_min: float = 0.0
    group_max: float = 0.0

    class Config:
        extra = "allow"
