from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class IAUsage(Base):
    __tablename__ = 'IAUsage'

    id = Column(Integer, primary_key=True)
    faculty = Column(String(50), unique=True, nullable=False,)
    usage_percentage = Column(Float, nullable=False)  # Latest usage
    latitude  = Column(Float, nullable=True)  # Para spike map
    longitude = Column(Float, nullable=True)  # Para spike map

    # Relación con datos históricos
    historical_data = relationship("IAUsageHistory", back_populates="usage")


class IAUsageHistory(Base):
    __tablename__ = 'IAUsageHistory'

    id = Column(Integer, primary_key=True)
    usage_id = Column(Integer, ForeignKey('IAUsage.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    usage_percentage = Column(Float, nullable=False)

    usage = relationship("IAUsage", back_populates="historical_data")