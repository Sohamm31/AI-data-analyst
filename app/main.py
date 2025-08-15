from fastapi import FastAPI
from app.api.v1.api import api_router
from app.db.database import engine, Base
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import all your SQLAlchemy models here
# This is crucial so that Base.metadata.create_all knows about them
from app.models import user, dataset, chat

# This single line of code finds all the classes that inherit from Base (your models)
# and creates the corresponding tables in the database if they don't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Data Analyst",
    description="An AI-powered data analysis tool with user accounts and chat history.",
    version="0.2.0"
)

# Include all the API routes from your api_router
app.include_router(api_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    """
    Serves the single-page frontend application.
    """
    return FileResponse('app/static/index.html')