# Main entry point for Emma AI Backend Application
from fastapi import FastAPI

app = FastAPI(title="Emma AI")


@app.get("/")
async def root():
    return {
        "status": "online",
        "assistant": "Emma",
    }