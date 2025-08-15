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
    """
    Endpoint for a logged-in user to upload a data file.
    1. Requires a valid JWT token for authentication.
    2. Processes the file and stores its data in a new database table.
    3. Creates a metadata record in the 'datasets' table, linking the file to the user.
    """
    try:
        # The file_handler service processes the raw file and returns the unique
        # name of the new table where the data is stored.
        table_name = await file_handler.process_and_store_file(file, db)
        
        # Create a new Dataset record to track this upload.
        new_dataset = dataset_model.Dataset(
            user_id=current_user.id,
            original_filename=file.filename,
            database_table_name=table_name
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        
        # Return the metadata of the newly created dataset record.
        return new_dataset
    except HTTPException as e:
        # Re-raise HTTPExceptions to let FastAPI handle them.
        raise e
    except Exception as e:
        # Catch any other unexpected errors during the process.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload: {str(e)}")
