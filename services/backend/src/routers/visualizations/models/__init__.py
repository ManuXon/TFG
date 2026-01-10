from .common import (
    CategoriesCounts,
    CategoriesValuesInt,
    CategoriesValuesFloat,
    AxisCountsWithTotal,
    LabelLevelsCounts,
    NamedSeriesInt,
    StackedDistribution,
    DualDemographicRow,
    DemographicDistributionSingle,
    DemographicDistributionDual,
    CorrelationRowBase,
)

from .survey import SurveySummaryResponse, SurveyFacultiesResponse, FacultyResponsesRow
from .faculty import FacultyScoresResponse, TreemapRow, SpikeMapRow
from .sankey import SankeyDataResponse
from .open_text import OpenTextAggregatesResponse, OpenTextItemsResponse, OpenTextItem, LabelsCounts
from .tools import ToolWordcountResponse
from .knowledge import KnowledgeFunctionalityCorrelationRow
from .uses import (
    UsesFunctionalityCorrelationRow,
    StudentsUsesByProposalRow,
    StudentsUsesAdequacyDistributionResponse,
    StudentsDocchangeByAdequacyResponse,
)
from .perceptions import TasksSupportDistributionResponse
from .training import TrainingInterestDistributionResponse
