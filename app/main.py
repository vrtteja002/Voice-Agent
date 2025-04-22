from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import voice
from app.config import API_HOST, API_PORT

app = FastAPI(
    title="Voice AI Agent",
    description="Conversational AI voice agent using OpenAI Agent SDK, Twilio, and GCP",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Voice AI Agent API is running. Access the documentation at /docs"}

# Health check endpoint
@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(voice.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)