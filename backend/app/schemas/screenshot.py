from datetime import datetime
from pydantic import BaseModel

class ScreenshotResponse(BaseModel):
    id: str
    trade_id: str
    url: str
    filename: str
    created_at: datetime
