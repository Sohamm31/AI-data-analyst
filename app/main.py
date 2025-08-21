from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
from app.db.database import engine, Base

from app.models import user, dataset, chat, saved_chart

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Data Analyst",
    description="An AI-powered data analysis tool with user accounts and chat history.",
    version="0.3.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse('app/static/index.html')

app.include_router(api_router, prefix="/api/v1")
