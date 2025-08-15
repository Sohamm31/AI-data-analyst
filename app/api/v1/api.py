from fastapi import APIRouter
from app.api.v1.endpoints import upload, chat, auth, datasets, charts

api_router = APIRouter()

# Add the new charts router
api_router.include_router(charts.router, prefix="/charts", tags=["Charts Gallery"])

# Existing routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets & History"])
api_router.include_router(upload.router, prefix="/data", tags=["Data Upload"])
api_router.include_router(chat.router, prefix="/query", tags=["Chat Query"])

