from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlalchemy.orm import Session
from app.services import ai_service
from app.core.config import settings
from app.db.database import get_db
from app.api.v1 import dependencies
from app.models import user as user_model, dataset as dataset_model, chat as chat_model

router = APIRouter()

@router.post("/chat")
async def chat_with_data(
    dataset_id: int = Body(...),
    question: str = Body(...),
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

    past_messages = db.query(chat_model.ChatMessage).filter(
        chat_model.ChatMessage.dataset_id == dataset_id
    ).order_by(chat_model.ChatMessage.timestamp.desc()).limit(10).all()
    past_messages.reverse() 

    conversation_history = ""
    for msg in past_messages:
        speaker = "Human" if msg.is_from_user else "AI"
        conversation_history += f"{speaker}: {msg.message}\n"
    
    full_prompt = conversation_history + f"Human: {question}"

    user_message = chat_model.ChatMessage(
        dataset_id=dataset.id,
        is_from_user=True,
        message=question
    )
    db.add(user_message)
    db.commit()

    response_dict = ai_service.get_sql_agent_response(
        db_uri=settings.DATABASE_URL,
        table_name=dataset.database_table_name,
        conversation_prompt=full_prompt
    )
    
    ai_message = chat_model.ChatMessage(
        dataset_id=dataset.id,
        is_from_user=False,
        message=response_dict["answer"]
    )
    db.add(ai_message)
    db.commit()

    return response_dict