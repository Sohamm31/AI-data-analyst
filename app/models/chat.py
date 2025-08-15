from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    is_from_user = Column(Boolean, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    dataset = relationship("Dataset", back_populates="chat_messages")
