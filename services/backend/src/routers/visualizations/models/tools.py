from pydantic import BaseModel


class ToolWordcountResponse(BaseModel):
    tool: str
    count: int = 0
    total: int = 0
    share: float = 0.0
