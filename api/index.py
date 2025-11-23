import sys
import os
from pathlib import Path

# Add the clova-rag-roadmap directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app from personalize_api
from app.personalize_api import app

# This is the entry point for Vercel
# Vercel will run this as: uvicorn api.index:app
