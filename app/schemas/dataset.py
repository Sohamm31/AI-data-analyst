from pydantic import BaseModel
from datetime import datetime

class Dataset(BaseModel):
    id: int
    original_filename: str
    upload_timestamp: datetime

    class Config:
        from_attributes = True
