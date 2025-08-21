from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import List

from app.db.database import get_db, engine
from app.api.v1 import dependencies
from app.models import user as user_model, dataset as dataset_model, chat as chat_model
from app.schemas import dataset as dataset_schema, chat as chat_schema
from app.services import ai_service

router = APIRouter()

@router.get("/", response_model=List[dataset_schema.Dataset])
def get_user_datasets(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):

    return db.query(dataset_model.Dataset).filter(dataset_model.Dataset.user_id == current_user.id).order_by(dataset_model.Dataset.upload_timestamp.desc()).all()


@router.get("/{dataset_id}/history", response_model=List[chat_schema.ChatMessage])
def get_dataset_chat_history(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):

    dataset = db.query(dataset_model.Dataset).filter(
        dataset_model.Dataset.id == dataset_id,
        dataset_model.Dataset.user_id == current_user.id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or you do not have permission to access it."
        )

    return db.query(chat_model.ChatMessage).filter(chat_model.ChatMessage.dataset_id == dataset_id).order_by(chat_model.ChatMessage.timestamp).all()


