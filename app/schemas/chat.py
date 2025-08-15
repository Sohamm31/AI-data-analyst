from pydantic import BaseModel
from datetime import datetime

class ChatMessage(BaseModel):
    id: int
    is_from_user: bool
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True
