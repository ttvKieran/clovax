from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.personalize_api import app as personalize_app

# Create main FastAPI app for Vercel
app = FastAPI(title="Naver TMW RAG API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the personalize app routes
app.mount("/api", personalize_app)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Naver TMW RAG API",
        "version": "1.0.0",
        "endpoints": {
            "personalized_roadmap": "/api/roadmap/personalized",
            "docs": "/docs"
        }
    }

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}
