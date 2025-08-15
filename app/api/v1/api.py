from fastapi import APIRouter
from app.api.v1.endpoints import upload, chat, auth, datasets

api_router = APIRouter()

# Router for user registration and login
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Router for managing datasets and retrieving chat histories
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets & History"])

# Router for uploading new data files
api_router.include_router(upload.router, prefix="/data", tags=["Data Upload"])

# Router for the main chat functionality
api_router.include_router(chat.router, prefix="/query", tags=["Chat Query"])
