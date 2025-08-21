from pydantic import BaseModel
from datetime import datetime
import json

class SavedChartBase(BaseModel):
    label: str
    chart_data: str 

class SavedChartCreate(SavedChartBase):
    pass

class SavedChart(SavedChartBase):
    id: int
    dataset_id: int
    created_at: datetime

    class Config:
        from_attributes = True