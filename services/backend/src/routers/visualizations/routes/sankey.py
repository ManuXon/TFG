from fastapi import APIRouter

from ..sankey_service import get_sankey_chart_data

from ..models.sankey import SankeyDataResponse

router = APIRouter()


@router.get("/sankey-data", response_model=SankeyDataResponse)
def sankey_data():
    return get_sankey_chart_data()
