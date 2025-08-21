from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.api.v1 import dependencies
from app.models import user as user_model, dataset as dataset_model, saved_chart as saved_chart_model
from app.schemas import saved_chart as saved_chart_schema

router = APIRouter()

@router.post("/datasets/{dataset_id}/charts", response_model=saved_chart_schema.SavedChart)
def save_chart_for_dataset(
    dataset_id: int,
    chart: saved_chart_schema.SavedChartCreate,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):

    dataset = db.query(dataset_model.Dataset).filter(
        dataset_model.Dataset.id == dataset_id,
        dataset_model.Dataset.user_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    new_chart = saved_chart_model.SavedChart(
        dataset_id=dataset_id,
        label=chart.label,
        chart_data=chart.chart_data
    )
    db.add(new_chart)
    db.commit()
    db.refresh(new_chart)
    return new_chart

@router.get("/datasets/{dataset_id}/charts", response_model=List[saved_chart_schema.SavedChart])
def get_charts_for_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):

    dataset = db.query(dataset_model.Dataset).filter(
        dataset_model.Dataset.id == dataset_id,
        dataset_model.Dataset.user_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    return db.query(saved_chart_model.SavedChart).filter(saved_chart_model.SavedChart.dataset_id == dataset_id).order_by(saved_chart_model.SavedChart.created_at.desc()).all()
