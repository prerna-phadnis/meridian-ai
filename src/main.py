from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.health import router as health_router
from src.routes.process import router as process_router 
from src.routes.notes import router as notes_router
from src.routes.citations import router as citations_router
from src.routes.chat import router as chat_router
from src.routes.delete import router as delete_router

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Meridian AI Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix="/api",
    tags=["health"]
)

app.include_router(
    process_router,
    prefix="/api",
    tags=["process"]
)

app.include_router(
    notes_router,
    prefix="/api",
    tags=["notes"]
)

app.include_router(
    citations_router,
    prefix="/api",
    tags=["citations"]
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["chat"]
)
app.include_router(
    delete_router, 
    prefix="/api", 
    tags=["delete"])  



@app.get("/")
async def root():
    return {
        "message": "🤖 Meridian AI Service",
        "status": "running"
    }


