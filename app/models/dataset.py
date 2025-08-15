from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    database_table_name = Column(String(255), unique=True, nullable=False)
    upload_timestamp = Column(DateTime, default=func.now())

    owner = relationship("User", back_populates="datasets")
    chat_messages = relationship("ChatMessage", back_populates="dataset", cascade="all, delete-orphan")
