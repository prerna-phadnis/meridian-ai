from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.health import router as health_router
from src.routes.process import router as process_router
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

@app.get("/")
async def root():
    return {
        "message": "🤖 Meridian AI Service",
        "status": "running"
    }