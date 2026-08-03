# Main entry point for Emma AI Backend Application
from fastapi import FastAPI
from app.routes.voice import router as voice_router

app = FastAPI(title="Emma AI")

app.include_router(voice_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "assistant": "Emma",
    }