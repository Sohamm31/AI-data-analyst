from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import file_handler
from app.api.v1 import dependencies
from app.models import user as user_model, dataset as dataset_model
from app.schemas import dataset as dataset_schema

router = APIRouter()

@router.post("/upload", response_model=dataset_schema.Dataset)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(dependencies.get_current_user)
):

    try:

        table_name = await file_handler.process_and_store_file(file, db)
        
        new_dataset = dataset_model.Dataset(
            user_id=current_user.id,
            original_filename=file.filename,
            database_table_name=table_name
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        
        return new_dataset
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload: {str(e)}")
