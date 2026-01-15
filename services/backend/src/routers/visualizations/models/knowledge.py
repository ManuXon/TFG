from pydantic import BaseModel
from .common import CorrelationRowBase


class KnowledgeFunctionalityCorrelationRow(CorrelationRowBase):
    knowledge_label: str
