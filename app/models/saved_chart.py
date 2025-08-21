from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class SavedChart(Base):
    __tablename__ = "saved_charts"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    label = Column(String(255), nullable=False)
    chart_data = Column(Text, nullable=False) 
    created_at = Column(DateTime, default=func.now())

    dataset = relationship("Dataset")
