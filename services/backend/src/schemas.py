from pydantic import BaseModel
from typing import List, Optional
import datetime


class IAUsageBase(BaseModel):
    faculty: str
    usage_percentage: float
    latitude: Optional[float]
    longitude: Optional[float]


class IAUsageCreate(IAUsageBase):
    pass


class IAUsage(IAUsageBase):
    id: int

    class Config:
        orm_mode = True


# Para datos históricos
class IAUsageHistoryBase(BaseModel):
    date: datetime.datetime
    usage_percentage: float


class IAUsageHistoryCreate(IAUsageHistoryBase):
    pass


class IAUsageHistory(IAUsageHistoryBase):
    id: int
    usage: Optional[IAUsage]

    class Config:
        orm_mode = True